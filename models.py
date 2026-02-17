from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint

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
from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, ForeignKey, Text
from sqlalchemy.orm import relationship

# ... (tu Student queda igual)

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    lichess_game_id = Column(String(32), nullable=False)
    played_at = Column(DateTime(timezone=True), nullable=True)

    speed = Column(String(20), nullable=True)       # bullet/blitz/rapid/classical/...
    perf = Column(String(30), nullable=True)        # blitz/rapid/etc (según venga)
    result = Column(String(20), nullable=True)      # win/loss/draw/unknown (lo calcularemos)

    pgn = Column(Text, nullable=True)               # opcional: guardar pgn
    json_raw = Column(Text, nullable=True)          # guardar la respuesta cruda si es NDJSON

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "lichess_game_id", name="uq_student_game"),
    )

    student = relationship("Student")
