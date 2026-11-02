from enum import Enum


class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    DRAW = "draw"
    WON = "won"
