from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, ForeignKey, Text
from sqlalchemy.orm import relationship

from db import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    level = Column(String(20), nullable=False)          # "primaria" | "bachillerato"
    grade = Column(String(20), nullable=True)           # "5", "6", "10", etc.
    lichess_username = Column(String(60), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("lichess_username", name="uq_students_lichess_username"),
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    lichess_game_id = Column(String(32), nullable=False)
    played_at = Column(DateTime(timezone=True), nullable=True)

    speed = Column(String(20), nullable=True)
    perf = Column(String(30), nullable=True)
    result = Column(String(20), nullable=True)

    pgn = Column(Text, nullable=True)
    json_raw = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "lichess_game_id", name="uq_student_game"),
    )

    student = relationship("Student")


# =========================
# Partidas en vivo (local)
# =========================

class LiveGame(Base):
    __tablename__ = "live_games"

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), nullable=False, default="waiting")  # waiting | active | finished

    white_player = Column(String(120), nullable=True)  # "student:12" o "guest:Ivan"
    black_player = Column(String(120), nullable=True)

    fen = Column(Text, nullable=False, default="startpos")  # luego lo cambiamos a FEN real

    moves = relationship("LiveMove", back_populates="game", cascade="all, delete-orphan")


class LiveMove(Base):
    __tablename__ = "live_moves"

    id = Column(Integer, primary_key=True, index=True)

    live_game_id = Column(Integer, ForeignKey("live_games.id", ondelete="CASCADE"), nullable=False)
    move_number = Column(Integer, nullable=False)

    uci = Column(String(10), nullable=False)
    san = Column(String(20), nullable=True)
    played_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    game = relationship("LiveGame", back_populates="moves")

    __table_args__ = (
        UniqueConstraint("live_game_id", "move_number", name="uq_live_game_move_number"),
    )
