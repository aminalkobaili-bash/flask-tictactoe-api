from uuid import uuid4
from sqlalchemy import Column, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from database import Base
from domain.model.game_status import GameStatus
from domain.model.game_type import GameType


class Game(Base):
    __tablename__ = "games"

    uuid = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    field_matrix = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    player1_uuid = Column(
        PG_UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=True
    )
    player2_uuid = Column(
        PG_UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=True
    )
    current_turn_uuid = Column(
        PG_UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=True
    )
    winner_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=True)

    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.WAITING)
    game_type = Column(Enum(GameType), nullable=False, default=GameType.COMPUTER)

    player1_symbol = Column(Integer, nullable=False, default=1)
    player2_symbol = Column(Integer, nullable=False, default=2)
