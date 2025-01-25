from abc import ABC, abstractmethod
from typing import Optional, Hashable

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
    def create_user_slot(self, slot_settings: int, permission_group: int) -> int:
        pass