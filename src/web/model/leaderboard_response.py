from uuid import UUID


class LeaderboardResponse:
    def __init__(self, user_uuid: UUID, login: str, win_ratio: float):
        self.uuid = str(user_uuid)
        self.login = login
        self.win_ratio = win_ratio

    def to_json(self) -> dict:
        return {"uuid": self.uuid, "login": self.login, "win_ratio": self.win_ratio}
