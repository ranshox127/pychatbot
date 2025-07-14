from domain.user_state import UserState, UserStateEnum, UserStateRepository


class UserStateAccessor:
    def __init__(self, user_state_repo: UserStateRepository):
        self.user_state_repo = user_state_repo
        # 這裡可以初始化資料庫連線池

    def get_state(self, user_id: str) -> UserStateEnum:
        state = self.user_state_repo.get(user_id)
        return state.status if state else UserStateEnum.IDLE

    def set_state(self, user_id: str, new_status: UserStateEnum):
        state = self.user_state_repo.get(user_id) or UserState(user_id)
        state.status = new_status
        self.user_state_repo.save(state)

    def reset_state(self, user_id: str):
        # 邏輯:
        # 1. 連線到 MySQL
        # 2. DELETE FROM user_states WHERE line_user_id = %s
        # 3. commit
        pass
