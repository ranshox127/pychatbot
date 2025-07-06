from abc import ABC, abstractmethod
from typing import Optional
from .state import UserState

class UserStateRepository(ABC):
    @abstractmethod
    def get(self, user_id: str) -> Optional[UserState]:
        pass

    @abstractmethod
    def set(self, state: UserState):
        pass

    @abstractmethod
    def delete(self, user_id: str):
        pass