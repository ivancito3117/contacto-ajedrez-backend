from __future__ import annotations

import json
from typing import Dict, Set, Optional

import chess
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from db import SessionLocal
from models import LiveGame, LiveMove


def _db() -> Session:
    return SessionLocal()


def _get_game_or_none(db: Session, game_id: int) -> LiveGame | None:
    game = db.query(LiveGame).filter(LiveGame.id == game_id).first()
    if not game:
        return None

    # Normaliza fen por si quedó "startpos"
    if not game.fen or game.fen == "startpos":
        game.fen = chess.STARTING_FEN
        db.commit()
        db.refresh(game)

    return game


def _load_board_from_game(game: LiveGame) -> chess.Board:
    fen = game.fen if game.fen and game.fen != "startpos" else chess.STARTING_FEN
    try:
        return chess.Board(fen)
    except Exception:
        return chess.Board(chess.STARTING_FEN)


def _next_move_number(db: Session, game_id: int) -> int:
    last = (
        db.query(LiveMove)
        .filter(LiveMove.live_game_id == game_id)
        .order_by(LiveMove.move_number.desc())
        .first()
    )
    return 1 if not last else int(last.move_number) + 1


class LiveGameHub:
    """
    Mantiene conexiones por game_id y permite broadcast a todos los clientes conectados.
    """
    def __init__(self) -> None:
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, game_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(game_id, set()).add(ws)

    def disconnect(self, game_id: int, ws: WebSocket) -> None:
        room = self.rooms.get(game_id)
        if not room:
            return
        room.discard(ws)
        if not room:
            self.rooms.pop(game_id, None)

    async def send(self, ws: WebSocket, payload: dict) -> None:
        await ws.send_text(json.dumps(payload, ensure_ascii=False))

    async def broadcast(self, game_id: int, payload: dict) -> None:
        room = self.rooms.get(game_id, set())
        if not room:
            return

        dead: Set[WebSocket] = set()
        msg = json.dumps(payload, ensure_ascii=False)

        for ws in room:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.add(ws)

        for ws in dead:
            self.disconnect(game_id, ws)


hub = LiveGameHub()


def _game_over_payload(board: chess.Board) -> Optional[dict]:
    if board.is_checkmate():
        winner = "black" if board.turn == chess.WHITE else "white"
        return {"type": "game_over", "reason": "checkmate", "winner": winner}

    if board.is_stalemate():
        return {"type": "game_over", "reason": "stalemate", "winner": None}

    if board.is_insufficient_material():
        return {"type": "game_over", "reason": "insufficient_material", "winner": None}

    if board.can_claim_threefold_repetition():
        return {"type": "game_over", "reason": "threefold_repetition_claimable", "winner": None}

    if board.can_claim_fifty_moves():
        return {"type": "game_over", "reason": "fifty_move_claimable", "winner": None}

    return None


async def ws_live_game(game_id: int, ws: WebSocket) -> None:
    await hub.connect(game_id, ws)
    db = _db()

    try:
        # 0) exigir que el juego exista (se crea por REST /live-games)
        game = _get_game_or_none(db, game_id)
        if not game:
            await hub.send(ws, {"type": "error", "message": "Game not found"})
            await ws.close(code=1008)
            return

        # 1) exigir identificación del cliente
        await hub.send(ws, {
            "type": "hello_required",
            "message": "Send {'type':'hello','player':'guest:Name'}"
        })

        raw0 = await ws.receive_text()
        try:
            hello = json.loads(raw0)
        except Exception:
            await hub.send(ws, {"type": "error", "message": "JSON inválido en hello"})
            await ws.close(code=1008)
            return

        if hello.get("type") != "hello" or not (hello.get("player") or "").strip():
            await hub.send(ws, {"type": "error", "message": "Debes enviar type=hello y player"})
            await ws.close(code=1008)
            return

        player = hello["player"].strip()

        # 2) validar que player esté unido y obtener lado
        side = None
        if game.white_player == player:
            side = "white"
        elif game.black_player == player:
            side = "black"
        else:
            await hub.send(ws, {
                "type": "error",
                "message": "Player not joined. Call POST /live-games/{id}/join"
            })
            await ws.close(code=1008)
            return

        # 3) enviar estado inicial
        board = _load_board_from_game(game)
        await hub.send(ws, {
            "type": "state",
            "game_id": game_id,
            "fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "status": game.status,
            "you_are": side,
        })

        # 4) loop de mensajes
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                await hub.send(ws, {"type": "error", "message": "JSON inválido"})
                continue

            msg_type = data.get("type")

            if msg_type == "ping":
                await hub.send(ws, {"type": "pong"})
                continue

            if msg_type != "move":
                await hub.send(ws, {"type": "error", "message": "Tipo no soportado"})
                continue

            uci = (data.get("uci") or "").strip()
            if not uci:
                await hub.send(ws, {"type": "error", "message": "Falta 'uci'"})
                continue

            # Re-cargar estado desde DB para que el backend sea la verdad
            game = _get_game_or_none(db, game_id)
            if not game:
                await hub.send(ws, {"type": "error", "message": "Game not found"})
                continue

            board = _load_board_from_game(game)

            # Validar turno según lado del jugador
            expected_turn = chess.WHITE if side == "white" else chess.BLACK
            if board.turn != expected_turn:
                await hub.send(ws, {"type": "move_rejected", "uci": uci, "reason": "no es tu turno"})
                continue

            # Validar UCI
            try:
                move = chess.Move.from_uci(uci)
            except Exception:
                await hub.send(ws, {"type": "move_rejected", "uci": uci, "reason": "uci inválido"})
                continue

            # Validar legalidad
            if move not in board.legal_moves:
                await hub.send(ws, {"type": "move_rejected", "uci": uci, "reason": "movimiento ilegal"})
                continue

            # Aplicar movimiento
            san = board.san(move)
            board.push(move)

            # Guardar jugada
            move_number = _next_move_number(db, game_id)
            db_move = LiveMove(
                live_game_id=game_id,
                move_number=move_number,
                uci=uci,
                san=san,
            )
            db.add(db_move)

            # Actualizar juego
            game.fen = board.fen()
            game.status = "active"
            db.commit()

            payload = {
                "type": "move_ok",
                "game_id": game_id,
                "uci": uci,
                "san": san,
                "fen": board.fen(),
                "turn": "white" if board.turn == chess.WHITE else "black",
                "move_number": move_number,
            }

            await hub.broadcast(game_id, payload)

            # Si terminó
            over = _game_over_payload(board)
            if over:
                game2 = _get_game_or_none(db, game_id)
                if game2:
                    game2.status = "finished"
                    game2.fen = board.fen()
                    db.commit()

                await hub.broadcast(game_id, {**over, "game_id": game_id, "fen": board.fen()})

    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(game_id, ws)
        db.close()
