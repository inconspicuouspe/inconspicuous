from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from uuid import uuid4
from datetime import datetime
from collections.abc import Hashable
from dataclasses import dataclass
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import DESCENDING
from .exceptions import NotFoundError, UserSlotTakenError
from . import authentication
from .consts import *

MAX_SESSIONS = 10

@dataclass(frozen=True)
class UserProfile:
    username: str
    user_id: str
    settings: authentication.Settings
    permission_group: int
    unfilled: bool

class Database(ABC, Hashable):
    def __hash__(self) -> int:
        return hash(id(self))

    @abstractmethod
    def get_username_by_session_data(self, session_data: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_login_data_by_username(self, username: str) -> Optional[tuple[str, str]]:
        pass

    @abstractmethod
    def add_session(self, session_data: str, username: str, session_name: str) -> None:
        pass

    @abstractmethod
    def create_user(self, username: str, login_data: str, login_token: str, user_slot: str) -> None:
        pass

    @abstractmethod
    def create_user_slot(self, slot_settings: int, permission_group: int, temp_name: str) -> str:
        pass

    @abstractmethod
    def has_username(self, username: str, *, except_user_id: Optional[str] = None) -> bool:
        pass
    
    @abstractmethod
    def list_sessions(self, username: str) -> list[authentication.Session]:
        pass
    
    @abstractmethod
    def get_session(self, session_data: str) -> Optional[authentication.Session]:
        pass
    
    @abstractmethod
    def delete_session(self, session_data: str) -> None:
        pass
    
    @abstractmethod
    def list_users(self) -> list[UserProfile]:
        pass
    
    @abstractmethod
    def get_correctly_cased_username(self, username: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def remove_unfilled_user(self, username: str) -> bool:
        pass
    
    @abstractmethod
    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        pass
    
    @abstractmethod
    def set_permission_group(self, username: str, permission_group: int) -> bool:
        pass
    
    @abstractmethod
    def set_settings(self, username: str, settings: int) -> bool:
        pass
    
    @abstractmethod
    def disable_user(self, username: str) -> Optional[str]:
        pass

class MongoDB(Database):
    client: MongoClient
    def __init__(self, uri: str, username: Optional[str] = None, password: Optional[str] = None, db: str = "main_db"):
        if username and password:
            uri = uri.format(username, password)
        self.client = self.connect(uri)
        self.db = self.client[db]
        self.users = self.db.users
        self.sessions = self.db.sessions

    @staticmethod
    def connect(uri: str) -> MongoClient:
        client: MongoClient = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        return client

    def create_user_slot(self, slot_settings, permission_group, temp_name):
        user_id = str(uuid4())
        self.users.insert_one({FIELD_USER_ID: user_id, FIELD_USERNAME: temp_name, FIELD_LOOKUP_USERNAME: temp_name.lower(), FIELD_UNFILLED: True, FIELD_SETTINGS: slot_settings, FIELD_PERMISSION_GROUP: permission_group})
        return user_id
    
    def create_user(self, username, login_data, login_token, user_slot):
        user_slot_data = self.users.find_one({FIELD_USER_SLOT: user_slot})
        if not user_slot_data:
            raise NotFoundError()
        if not user_slot_data.get(FIELD_UNFILLED):
            raise UserSlotTakenError()
        self.users.update_one({FIELD_USER_SLOT: user_slot}, {"$set":
            {
                FIELD_UNFILLED: False,
                FIELD_USERNAME: username,
                FIELD_LOGIN_DATA: login_data,
                FIELD_LOGIN_TOKEN: login_token,
                FIELD_LOOKUP_USERNAME: username.lower()
            }
        })

    def get_login_data_by_username(self, username):
        user_data = self.users.find_one({FIELD_LOOKUP_USERNAME: username.lower()})
        if not user_data:
            return None
        if FIELD_LOGIN_DATA not in user_data:
            return None
        if FIELD_LOGIN_TOKEN not in user_data:
            return None
        login_data = user_data[FIELD_LOGIN_DATA]
        login_token = user_data[FIELD_LOGIN_TOKEN]
        assert isinstance(login_data, str)
        assert isinstance(login_token, str)
        return (login_data, login_token)

    def has_username(self, username, *, except_user_id = None):
        user = self.users.find_one({FIELD_LOOKUP_USERNAME: username.lower(), FIELD_USER_SLOT: {"$ne": except_user_id}})
        return bool(user)
    
    def get_username_by_session_data(self, session_data):
        session = self.sessions.find_one({FIELD_SESSION_DATA: session_data})
        if not session:
            return None
        if FIELD_USERNAME not in session:
            return None
        username = session[FIELD_USERNAME]
        assert isinstance(username, str)
        return username

    def add_session(self, session_data, username, session_name):
        if not self.has_username(username):
            raise NotFoundError()
        self.sessions.insert_one({
            FIELD_SESSION_DATA: session_data,
            FIELD_SESSION_NAME: session_name,
            FIELD_LOOKUP_USERNAME: username.lower(),
            FIELD_USERNAME: username,
            FIELD_CREATION_TIME: datetime.now()
        })
        sessions = list(self.sessions.find({FIELD_LOOKUP_USERNAME: username.lower()}).sort(FIELD_CREATION_TIME, DESCENDING).limit(MAX_SESSIONS + 1))
        if len(sessions) == MAX_SESSIONS + 1:
            self.sessions.delete_many({"_id": {"$not": {"$in": [sess["_id"] for sess in sessions[:MAX_SESSIONS]]}}, FIELD_LOOKUP_USERNAME: username.lower()})
    
    def list_sessions(self, username):
        account = self.users.find_one({FIELD_LOOKUP_USERNAME: username.lower()})
        return [authentication.Session(document.get(FIELD_SESSION_DATA), document.get(FIELD_CREATION_TIME), username, document.get(FIELD_SESSION_NAME), authentication.Settings(account.get(FIELD_SETTINGS)), account.get(FIELD_PERMISSION_GROUP)) for document in self.sessions.find({FIELD_LOOKUP_USERNAME: username.lower()})]

    def get_session(self, session_data):
        session = self.sessions.find_one({FIELD_SESSION_DATA: session_data})
        account = self.users.find_one({FIELD_LOOKUP_USERNAME: session.get(FIELD_LOOKUP_USERNAME)})
        if not session:
            return None
        return authentication.Session(session.get(FIELD_SESSION_DATA), session.get(FIELD_CREATION_TIME), session.get(FIELD_USERNAME), session.get(FIELD_SESSION_NAME), authentication.Settings(account.get(FIELD_SETTINGS)), account.get(FIELD_PERMISSION_GROUP))
    
    def delete_session(self, session_data):
        self.sessions.delete_one({FIELD_SESSION_DATA: session_data})
    
    def list_users(self):
        return [
            UserProfile(document.get(FIELD_USERNAME, "???"), document.get(FIELD_USER_ID, "???"), authentication.Settings(document.get(FIELD_SETTINGS, 0)), document.get(FIELD_PERMISSION_GROUP), document.get(FIELD_UNFILLED))
            for document in self.users.find()
        ]
    
    def get_correctly_cased_username(self, username):
        document = self.users.find_one({FIELD_LOOKUP_USERNAME: username.lower()})
        if document is None:
            return None
        return document.get(FIELD_USERNAME)
    
    def remove_unfilled_user(self, username):
        document = self.users.find_one_and_delete({FIELD_UNFILLED: True, FIELD_LOOKUP_USERNAME: username.lower()})
        return document is not None
    
    def get_user_profile(self, username):
        document = self.users.find_one({FIELD_LOOKUP_USERNAME: username.lower()})
        return UserProfile(document.get(FIELD_USERNAME, "???"), document.get(FIELD_USER_ID, "???"), authentication.Settings(document.get(FIELD_SETTINGS, 0)), document.get(FIELD_PERMISSION_GROUP), document.get(FIELD_UNFILLED))
    
    def set_permission_group(self, username, permission_group):
        document = self.users.find_one_and_update({FIELD_LOOKUP_USERNAME: username.lower()}, {"$set": {FIELD_PERMISSION_GROUP: permission_group}})
        return document is not None
    
    def set_settings(self, username, settings):
        document = self.users.find_one_and_update({FIELD_LOOKUP_USERNAME: username.lower()}, {"$set": {FIELD_SETTINGS: settings}})
        return document is not None
    
    def disable_user(self, username):
        user_id = str(uuid4())
        document = self.users.find_one_and_update({FIELD_LOOKUP_USERNAME: username.lower(), FIELD_UNFILLED: False}, {"$set": {FIELD_UNFILLED: True, FIELD_USER_SLOT: user_id}, "$unset": {FIELD_LOGIN_DATA: ""}})
        if document is not None:
            self.sessions.delete_many({FIELD_LOOKUP_USERNAME: username.lower()})
        return user_id if document is not None else None