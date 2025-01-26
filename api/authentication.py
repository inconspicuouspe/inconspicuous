from hashlib import sha3_512
from io import BytesIO
from typing import Optional, Self
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass
from hmac import compare_digest
from enum import Flag, auto
from datetime import datetime
import secrets, sys, logging
from cachetools import LRUCache, cached
from flask import Response, Request
from . import database as _database
from .exceptions import NotFoundError, AlreadyExistsError

@dataclass
class LoginData:
    data: str
    login_token: int

@dataclass
class SessionData:
    data: str
    @classmethod
    def from_request(cls, request: Request) -> Optional[Self]:
        if SESSION_DATA_COOKIE_NAME not in request.cookies:
            return None
        return cls(request.cookies[SESSION_DATA_COOKIE_NAME])

@dataclass
class Session:
    session_data: SessionData
    creation_time: datetime
    username: str
    session_name: str

class Settings(Flag):
    VIEW_MEMBERS = auto()
    _VIEW_MEMBER_SETTINGS = auto()
    VIEW_MEMBER_SETTINGS = VIEW_MEMBERS | _VIEW_MEMBER_SETTINGS
    _EDIT_MEMBER_SETTINGS = auto()
    EDIT_MEMBER_SETTINGS = VIEW_MEMBER_SETTINGS | _EDIT_MEMBER_SETTINGS
    _CREATE_MEMBERS = auto()
    CREATE_MEMBERS = VIEW_MEMBERS | _CREATE_MEMBERS
    _DISABLE_MEMBERS = auto()
    DISABLE_MEMBERS = VIEW_MEMBERS | _DISABLE_MEMBERS
    SYS_ADMIN = auto()

encode_b64 = urlsafe_b64encode
decode_b64 = urlsafe_b64decode

SESSION_DATA_COOKIE_NAME = "session_data"
VALID_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
USERNAME_MAX_LENGTH = 32
USERNAME_MIN_LENGTH = 3
PASSWORD_MAX_LENGTH = 65535
PASSWORD_MIN_LENGTH = 5

def validate_username_and_password(username: str, password: str) -> Optional[str]:
    if len(username) < USERNAME_MIN_LENGTH:
        return f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters long."
    if len(username) > USERNAME_MAX_LENGTH:
        return f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters long."
    for char in username:
        if char not in VALID_CHARACTERS:
            return "Username must consist of characters a-z, A-Z, 0-9 and _."
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters long."
    if len(password) > PASSWORD_MAX_LENGTH:
        return f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters long."
    return None

def create_login_data(username: str, password: str, login_token: Optional[int] = None) -> LoginData:
    assert not validate_username_and_password(username, password)
    unhashed_data = BytesIO()
    unhashed_data.write(len(username).to_bytes(1))
    unhashed_data.write(username.encode("utf-8"))
    unhashed_data.write(len(password).to_bytes(2))
    unhashed_data.write(password.encode("utf-8"))
    login_token = login_token or secrets.randbits(31)
    unhashed_data.write(login_token.to_bytes(8))
    hashed_data = sha3_512(unhashed_data.getbuffer()).digest()
    return LoginData(encode_b64(hashed_data).decode("utf-8"), login_token)

def lookup_user_login_data(database: _database.Database, username: str) -> LoginData:
    data = database.get_login_data_by_username(username)
    if data is None:
        raise NotFoundError()
    return LoginData(*data)

def create_session_data() -> SessionData:
    return SessionData(secrets.token_urlsafe(256))

def lookup_user_by_session_data(database: _database.Database, session_data: str) -> str:
    user = database.get_username_by_session_data(session_data)
    if user is None:
        raise NotFoundError()
    return user

def make_user(database: _database.Database, username: str, password: str, session_name: str, user_slot: int) -> SessionData:
    if database.has_username(username, except_user_id=user_slot):
        raise AlreadyExistsError()
    login_data = create_login_data(username, password)
    database.create_user(username, login_data.data, login_data.login_token, user_slot)
    return make_session(database, username, session_name)

def make_session(database: _database.Database, username: str, session_name: str) -> SessionData:
    session_data = create_session_data()
    database.add_session_data(session_data.data, username, session_name)
    return session_data

@cached(cache=LRUCache(1<<16, sys.getsizeof))
def check_session(database: _database.Database, session_data: SessionData) -> Optional[str]:
    try:
        user = lookup_user_by_session_data(database, session_data.data)
        return user
    except NotFoundError:
        return None

def login(database: _database.Database, username: str, password: str, session_name: str) -> Optional[SessionData]:
    if not database.has_username(username):
        logging.debug("User does not exist.")
        logging.debug(str(database.users.find_one({"username": username})))
        return None
    try:
        logging.debug("User exists.")
        user_login_data = lookup_user_login_data(database, username)
        generated_login_data = create_login_data(username, password, user_login_data.login_token)
        success = compare_digest(user_login_data.data, generated_login_data.data)
        if not success:
            logging.debug("Password is incorrect.")
            return None
        logging.debug("Password is correct")
        return make_session(database, username, session_name)
    except NotFoundError:
        return None

create_account = make_user

def create_user_slot(database: _database.Database, settings: Settings, permission_group: int, temp_name: str) -> int:
    if database.has_username(temp_name):
        raise AlreadyExistsError()
    numeric_settings = settings.value
    return database.create_user_slot(numeric_settings, permission_group, temp_name)

def logout(response: Response):
    response.set_cookie("session_data", "", expires=0)

def modify_response(database: _database.Database, response: Response, request: Request) -> Response:
    session_data = SessionData.from_request(request)
    if session_data is None:
        return response
    if not check_session(database, session_data):
        logout(response)
    return response