from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum, auto
from dataclasses import dataclass, field


class UserStateEnum(Enum):
    IDLE = auto()
    AWAITING_REGISTRATION_ID = auto()
    AWAITING_LEAVE_REASON = auto()
    AWAITING_TA_QUESTION = auto()
    AWAITING_CONTENTS_NAME = auto()
    AWAITING_REGRADE_BY_TA_REASON = auto()


@dataclass
class UserState:
    line_user_id: str
    status: UserStateEnum = UserStateEnum.IDLE
    context: dict = field(default_factory=dict)


class UserStateRepository(ABC):
    @abstractmethod
    def get(self, line_user_id: str) -> Optional[UserState]:
        pass

    @abstractmethod
    def save(self, state: UserState):
        pass

    @abstractmethod
    def delete(self, line_user_id: str):
        pass
