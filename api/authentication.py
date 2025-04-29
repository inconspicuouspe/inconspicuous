from __future__ import annotations
from hashlib import sha3_512
from io import BytesIO
from typing import Optional, Self
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass
from hmac import compare_digest
from enum import Flag, auto
from datetime import datetime
import secrets, uuid, sys, logging
from cachetools import LRUCache, cached, TTLCache
from flask import Response, Request
from . import database as _database
from . import consts
from .exceptions import (
    NotFoundError,
    AlreadyExistsError,
    PasswordTooLong,
    PasswordTooShort,
    UsernameTooLong,
    UsernameTooShort,
    UsernameInvalidCharacters,
    InvalidCredentials,
    NoSession,
    CannotBeNamedAnonymous
)

@dataclass(frozen=True)
class LoginData:
    data: str
    login_token: str

@dataclass(frozen=True)
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
    settings: Settings
    permission_group: int
    @classmethod
    def create_empty_session(cls) -> Self:
        return cls(SessionData(""), datetime.now(), ANONYMOUS_USERNAME, ANONYMOUS_USERNAME, Settings.NONE, 1 - (1 << 31))
    
    @cached(TTLCache(256, 60))
    @staticmethod
    def from_session_data(database: _database.Database, session_data: SessionData) -> Session:
        session = database.get_session(session_data.data)
        if session is None:
            raise NoSession
        return session
    
    def is_empty(self) -> bool:
        return not self
    
    def __bool__(self) -> bool:
        return self.username != ANONYMOUS_USERNAME

class Settings(Flag):
    NONE = 0
    VIEW_MEMBERS = auto()
    _VIEW_MEMBER_SETTINGS = auto()
    VIEW_MEMBER_SETTINGS = VIEW_MEMBERS | _VIEW_MEMBER_SETTINGS
    _EDIT_MEMBER_SETTINGS = auto()
    EDIT_MEMBER_SETTINGS = VIEW_MEMBER_SETTINGS | _EDIT_MEMBER_SETTINGS
    _CREATE_MEMBERS = auto()
    CREATE_MEMBERS = VIEW_MEMBERS | _CREATE_MEMBERS
    _DISABLE_MEMBERS = auto()
    DISABLE_MEMBERS = VIEW_MEMBERS | _DISABLE_MEMBERS
    _VIEW_INVITED_MEMBERS = auto()
    VIEW_INVITED_MEMBERS = VIEW_MEMBERS | _VIEW_INVITED_MEMBERS
    _UNINVITE_MEMBERS = auto()
    UNINVITE_MEMBERS = VIEW_INVITED_MEMBERS | _UNINVITE_MEMBERS
    ADMIN = (1 << 20) - 1
    SYS_ADMIN = (1 << 31) - 1 # Has to be last
    def get_translated_name(self):
        return consts.SETTINGS_NAME_TRANSLATIONS.get(self.name) or "intern: " + self.name

encode_b64 = urlsafe_b64encode
decode_b64 = urlsafe_b64decode

SESSION_DATA_COOKIE_NAME = "session_data"
VALID_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
ANONYMOUS_USERNAME = "anonymous"
USERNAME_MAX_LENGTH = 32
USERNAME_MIN_LENGTH = 3
PASSWORD_MAX_LENGTH = 1024
PASSWORD_MIN_LENGTH = 5

def validate_username_and_password(username: str, password: str) -> None:
    username_constraints(username)
    password_constraints(password)

def username_constraints(username: str) -> None:
    if username.lower() == ANONYMOUS_USERNAME.lower():
        raise CannotBeNamedAnonymous()
    if len(username) < USERNAME_MIN_LENGTH:
        raise UsernameTooShort("Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters long.")
    if len(username) > USERNAME_MAX_LENGTH:
        raise UsernameTooLong(f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters long.")
    for char in username:
        if char not in VALID_CHARACTERS:
            raise UsernameInvalidCharacters("Username must consist of characters a-z, A-Z, 0-9, _ and -.")

def password_constraints(password: str):
    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordTooShort(f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters long.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordTooLong(f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters long.")

def create_login_data(username: str, password: str, login_token: Optional[str] = None) -> LoginData:
    unhashed_data = BytesIO()
    unhashed_data.write(len(username).to_bytes(1))
    unhashed_data.write(username.encode("utf-8"))
    unhashed_data.write(len(password).to_bytes(2))
    unhashed_data.write(password.encode("utf-8"))
    login_token = login_token or str(uuid.uuid4())
    unhashed_data.write(login_token.encode("utf-8"))
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

def make_user(database: _database.Database, username: str, password: str, session_name: str, user_slot: str) -> SessionData:
    if database.has_username(username, except_user_id=user_slot):
        raise AlreadyExistsError()
    login_data = create_login_data(username, password)
    database.create_user(username, login_data.data, login_data.login_token, user_slot)
    return make_session(database, username, session_name)

def make_session(database: _database.Database, username: str, session_name: str) -> SessionData:
    session_data = create_session_data()
    database.add_session(session_data.data, username, session_name)
    return session_data

def remove_unfilled_user(database: _database.Database, username: str) -> None:
    success = database.remove_unfilled_user(username)
    if not success:
        raise NotFoundError()

@cached(cache=LRUCache(1<<16, sys.getsizeof))
def check_session(database: _database.Database, session_data: SessionData) -> str:
    user = lookup_user_by_session_data(database, session_data.data)
    return user

def login(database: _database.Database, username: str, password: str, session_name: str) -> SessionData:
    if not database.has_username(username):
        raise NotFoundError()
    user_login_data = lookup_user_login_data(database, username)
    username = database.get_correctly_cased_username(username)
    if username is None:
        raise NotFoundError()
    generated_login_data = create_login_data(username, password, user_login_data.login_token)
    success = compare_digest(user_login_data.data, generated_login_data.data)
    if not success:
        raise InvalidCredentials()
    return make_session(database, username, session_name)

def sign_up(database: _database.Database, username: str, password: str, session_name: str, user_slot: str) -> SessionData:
    validate_username_and_password(username, password)
    return make_user(database, username, password, session_name, user_slot)

def create_user_slot(database: _database.Database, settings: Settings, permission_group: int, temp_name: str) -> str:
    if database.has_username(temp_name):
        raise AlreadyExistsError()
    numeric_settings = settings.value
    return database.create_user_slot(numeric_settings, permission_group, temp_name)

def logout(database: _database.Database, response: Response, request: Request) -> Response:
    session_data = SessionData.from_request(request)
    if session_data is None:
        return response
    database.delete_session(session_data.data)
    response.set_cookie("session_data", "", expires=0)
    return response

def extract_session(database: _database.Database, request: Request) -> Session:
    session_data = SessionData.from_request(request)
    if session_data is None:
        raise NoSession()
    return Session.from_session_data(database, session_data)

def extract_session_or_empty(database: _database.Database, request: Request) -> Session:
    try:
        return extract_session(database, request)
    except NoSession:
        return Session.create_empty_session()