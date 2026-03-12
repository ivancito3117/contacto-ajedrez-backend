from __future__ import annotations

from typing import Optional, Literal

import chess
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db import get_db
from models import LiveGame


router = APIRouter(prefix="/live-games", tags=["live-games"])


# --------- Schemas ---------

PlayerSide = Literal["white", "black"]


class LiveGameCreateIn(BaseModel):
    white_player: Optional[str] = Field(default=None, description='Ej: "student:12" o "guest:Ivan"')
    black_player: Optional[str] = Field(default=None, description='Ej: "student:7" o "guest:Paula"')


class LiveGameJoinIn(BaseModel):
    player: str = Field(..., min_length=1, max_length=120, description='Ej: "student:12" o "guest:Ivan"')
    side: Optional[PlayerSide] = Field(default=None, description="Si no se envía, el servidor asigna un lado disponible.")


class LiveGameOut(BaseModel):
    id: int
    status: str
    fen: str
    turn: PlayerSide
    white_player: Optional[str]
    black_player: Optional[str]
    ws_url: str


# --------- Helpers ---------

def _turn_from_fen(fen: str) -> PlayerSide:
    board = chess.Board(fen)
    return "white" if board.turn == chess.WHITE else "black"


def _ws_url(request: Request, game_id: int) -> str:
    # Esto construye URL tipo ws://10.x.x.x:8000/ws/games/1 según el host que uses
    host = request.headers.get("host", "localhost:8000")
    # Si algún proxy manda X-Forwarded-Proto, lo respetamos
    proto = request.headers.get("x-forwarded-proto", "http")
    ws_proto = "wss" if proto == "https" else "ws"
    return f"{ws_proto}://{host}/ws/games/{game_id}"


# --------- Endpoints ---------

@router.post("", response_model=LiveGameOut)
def create_live_game(payload: LiveGameCreateIn, request: Request, db: Session = Depends(get_db)):
    game = LiveGame(
        status="waiting",
        white_player=payload.white_player,
        black_player=payload.black_player,
        fen=chess.STARTING_FEN,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    return LiveGameOut(
        id=game.id,
        status=game.status,
        fen=game.fen,
        turn=_turn_from_fen(game.fen),
        white_player=game.white_player,
        black_player=game.black_player,
        ws_url=_ws_url(request, game.id),
    )


@router.get("/{game_id}", response_model=LiveGameOut)
def get_live_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    game = db.query(LiveGame).filter(LiveGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Live game not found")

    # Normalizamos por si quedó "startpos"
    fen = game.fen if game.fen and game.fen != "startpos" else chess.STARTING_FEN

    return LiveGameOut(
        id=game.id,
        status=game.status,
        fen=fen,
        turn=_turn_from_fen(fen),
        white_player=game.white_player,
        black_player=game.black_player,
        ws_url=_ws_url(request, game.id),
    )


@router.post("/{game_id}/join", response_model=LiveGameOut)
def join_live_game(game_id: int, payload: LiveGameJoinIn, request: Request, db: Session = Depends(get_db)):
    game = db.query(LiveGame).filter(LiveGame.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Live game not found")

    # Si la partida ya terminó, no dejamos unir
    if game.status == "finished":
        raise HTTPException(status_code=400, detail="Game already finished")

    # Asignación de lado
    side = payload.side

    if side is None:
        # Asignar automáticamente lado disponible
        if not game.white_player:
            side = "white"
        elif not game.black_player:
            side = "black"
        else:
            raise HTTPException(status_code=409, detail="Game already has two players")

    if side == "white":
        if game.white_player and game.white_player != payload.player:
            raise HTTPException(status_code=409, detail="White side already taken")
        game.white_player = payload.player
    else:
        if game.black_player and game.black_player != payload.player:
            raise HTTPException(status_code=409, detail="Black side already taken")
        game.black_player = payload.player

    # Si ya hay ambos jugadores, activamos
    if game.white_player and game.black_player:
        game.status = "active"
    else:
        game.status = "waiting"

    # Normalizamos FEN
    if not game.fen or game.fen == "startpos":
        game.fen = chess.STARTING_FEN

    db.commit()
    db.refresh(game)

    return LiveGameOut(
        id=game.id,
        status=game.status,
        fen=game.fen,
        turn=_turn_from_fen(game.fen),
        white_player=game.white_player,
        black_player=game.black_player,
        ws_url=_ws_url(request, game.id),
    )
