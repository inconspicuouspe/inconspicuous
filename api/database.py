from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from secrets import randbits
from datetime import datetime
from collections.abc import Hashable
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from exceptions import NotFoundError, UserSlotTakenError
from . import authentication

class Database(ABC, Hashable):
    def __hash__(self) -> int:
        return hash(id(self))

    @abstractmethod
    def get_username_by_session_data(self, session_data: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_login_data_by_username(self, username: str) -> Optional[tuple[str, int]]:
        pass

    @abstractmethod
    def add_session_data(self, session_data: str, username: str, session_name: str) -> None:
        pass

    @abstractmethod
    def create_user(self, username: str, login_data: str, login_token: int, user_slot: int) -> None:
        pass

    @abstractmethod
    def create_user_slot(self, slot_settings: int, permission_group: int, temp_name: str) -> int:
        pass

    @abstractmethod
    def has_username(self, username: str, *, except_user_id: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    def list_sessions(self, username: str) -> list[authentication.Session]:
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
        user_id = randbits(32)
        self.users.insert_one({"user_id": user_id, "username": temp_name, "unfilled": True, "settings": slot_settings, "permission_group": permission_group})
        return user_id
    
    def create_user(self, username, login_data, login_token, user_slot):
        user_slot_data = self.users.find_one({"user_id": user_slot})
        if not user_slot:
            raise NotFoundError()
        if not user_slot_data.get("unfilled"):
            raise UserSlotTakenError()
        self.users.update_one({"user_id": user_slot}, {"$set":
            {
                "unfilled": False,
                "username": username,
                "login_data": login_data,
                "login_token": login_token
            }
        })

    def get_login_data_by_username(self, username):
        user_data = self.users.find_one({"username": username})
        if not user_data:
            return None
        if "login_data" not in user_data:
            return None
        if "login_token" not in user_data:
            return None
        login_data = user_data["login_data"]
        login_token = user_data["login_token"]
        assert isinstance(login_data, str)
        assert isinstance(login_token, int)
        return (login_data, login_token)

    def has_username(self, username, *, except_user_id = None):
        user = self.users.find_one({"username": username})
        if user and user.get("user_id") == except_user_id:
            return False
        return bool(user)
    
    def get_username_by_session_data(self, session_data):
        session = self.sessions.find_one({"session_data": session_data})
        if not session:
            return None
        if "username" not in session:
            return None
        username = session["username"]
        assert isinstance(username, str)
        return username

    def add_session_data(self, session_data, username, session_name):
        if not self.has_username(username):
            raise NotFoundError()
        self.sessions.insert_one({
            "session_data": session_data,
            "session_name": session_name,
            "username": username,
            "creation_time": datetime.now()
        })
    
    def list_sessions(self, username):
        return [authentication.Session(document.get("session_data"), document.get("creation_time"), username, document.get("session_name")) for document in self.sessions.find({"username": username})]