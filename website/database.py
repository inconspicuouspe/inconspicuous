from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def user_by_session_data(self, session_data: str) -> str:
        pass