from enum import Enum, auto
from dataclasses import dataclass, field
from domain.user_state_repository import UserStateRepository
import json
import pymysql # Or your preferred DB library

class UserStateEnum(Enum):
    """定義所有可能的對話狀態"""
    IDLE = auto()
    AWAITING_REGISTRATION_ID = auto()
    AWAITING_LEAVE_REASON = auto()
    AWAITING_TA_QUESTION = auto()

@dataclass
class UserState:
    """代表一個用戶的完整狀態物件"""
    user_id: str
    status: UserStateEnum = UserStateEnum.IDLE
    context: dict = field(default_factory=dict)
    
class StateManagementService:
    def __init__(self, user_state_repo: UserStateRepository):
        self.user_state_repo = user_state_repo
        # 這裡可以初始化資料庫連線池

    def get_state(self, user_id: str) -> UserState:
        # 邏輯:
        # 1. 連線到 MySQL
        # 2. SELECT state_name, context FROM user_states WHERE line_user_id = %s
        # 3. 如果有找到資料：
        #    - state_name = row['state_name']
        #    - context = json.loads(row['context'])
        #    - return UserState(user_id, UserStateEnum[state_name], context)
        # 4. 如果沒找到：
        #    - return UserState(user_id) # 回傳預設的 IDLE 狀態
        pass

    def set_state(self, state: UserState):
        # 邏輯:
        # 1. 連線到 MySQL
        # 2. context_json = json.dumps(state.context)
        # 3. state_name = state.status.name
        # 4. 執行 INSERT ... ON DUPLICATE KEY UPDATE ...
        #    - `line_user_id` = state.user_id
        #    - `state_name` = state_name
        #    - `context` = context_json
        # 5. commit
        pass

    def reset_state(self, user_id: str):
        # 邏輯:
        # 1. 連線到 MySQL
        # 2. DELETE FROM user_states WHERE line_user_id = %s
        # 3. commit
        pass