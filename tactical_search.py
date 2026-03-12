from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tactics_detector import analyze_tactics


@dataclass
class EngineLine:
    multipv: int
    depth: int
    score_cp: Optional[int]
    score_mate: Optional[int]
    pv: List[str]


class StockfishUciEngine:
    def __init__(self, engine_path: str) -> None:
        self.engine_path = engine_path
        self.proc: Optional[subprocess.Popen[str]] = None

    def start(self) -> None:
        if self.proc is not None:
            return

        self.proc = subprocess.Popen(
            [self.engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        self._send("uci")
        self._read_until("uciok")
        self._send("isready")
        self._read_until("readyok")

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            self._send("quit")
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        self.proc = None

    def _send(self, cmd: str) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("El motor no está iniciado")
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _read_line(self) -> str:
        if self.proc is None or self.proc.stdout is None:
            raise RuntimeError("El motor no está iniciado")
        line = self.proc.stdout.readline()
        if line == "":
            raise RuntimeError("Stockfish cerró la salida inesperadamente")
        return line.strip()

    def _read_until(self, token: str) -> List[str]:
        lines: List[str] = []
        while True:
            line = self._read_line()
            lines.append(line)
            if line == token:
                return lines

    def get_top_lines(self, fen: str, depth: int = 3, multipv: int = 5) -> List[EngineLine]:
        self.start()

        self._send(f"setoption name MultiPV value {multipv}")
        self._send("isready")
        self._read_until("readyok")

        self._send(f"position fen {fen}")
        self._send(f"go depth {depth}")

        best_lines: Dict[int, EngineLine] = {}

        while True:
            line = self._read_line()

            if line.startswith("info "):
                parsed = self._parse_info_line(line)
                if parsed is not None and parsed.pv:
                    best_lines[parsed.multipv] = parsed

            elif line.startswith("bestmove"):
                break

        return [best_lines[k] for k in sorted(best_lines.keys())]

    def _parse_info_line(self, line: str) -> Optional[EngineLine]:
        tokens = line.split()

        if "pv" not in tokens:
            return None

        try:
            depth = int(tokens[tokens.index("depth") + 1]) if "depth" in tokens else 0
            multipv = int(tokens[tokens.index("multipv") + 1]) if "multipv" in tokens else 1
        except (ValueError, IndexError):
            return None

        score_cp: Optional[int] = None
        score_mate: Optional[int] = None

        if "score" in tokens:
            try:
                score_idx = tokens.index("score")
                score_type = tokens[score_idx + 1]
                score_value = tokens[score_idx + 2]
                if score_type == "cp":
                    score_cp = int(score_value)
                elif score_type == "mate":
                    score_mate = int(score_value)
            except (ValueError, IndexError):
                pass

        pv_idx = tokens.index("pv")
        pv = tokens[pv_idx + 1 :]

        return EngineLine(
            multipv=multipv,
            depth=depth,
            score_cp=score_cp,
            score_mate=score_mate,
            pv=pv,
        )


def fen_board_only(fen: str) -> str:
    return fen.split()[0]


def parse_fen_parts(fen: str) -> List[str]:
    parts = fen.split()
    if len(parts) < 4:
        raise ValueError("FEN inválido")
    while len(parts) < 6:
        if len(parts) == 4:
            parts.append("0")
        elif len(parts) == 5:
            parts.append("1")
    return parts


def square_to_index(square: str) -> int:
    files = "abcdefgh"
    file_idx = files.index(square[0])
    rank_idx = int(square[1]) - 1
    return rank_idx * 8 + file_idx


def index_to_square(index: int) -> str:
    files = "abcdefgh"
    return f"{files[index % 8]}{(index // 8) + 1}"


def fen_piece_to_board_map(board_part: str) -> Dict[int, str]:
    rows = board_part.split("/")
    board: Dict[int, str] = {}
    rank = 7
    for row in rows:
        file_idx = 0
        for ch in row:
            if ch.isdigit():
                file_idx += int(ch)
            else:
                sq = rank * 8 + file_idx
                board[sq] = ch
                file_idx += 1
        rank -= 1
    return board


def board_map_to_fen(board: Dict[int, str]) -> str:
    rows: List[str] = []
    for rank in range(7, -1, -1):
        row = ""
        empty_count = 0
        for file_idx in range(8):
            sq = rank * 8 + file_idx
            piece = board.get(sq)
            if piece is None:
                empty_count += 1
            else:
                if empty_count:
                    row += str(empty_count)
                    empty_count = 0
                row += piece
        if empty_count:
            row += str(empty_count)
        rows.append(row)
    return "/".join(rows)


def toggle_side(side: str) -> str:
    return "b" if side == "w" else "w"


def apply_uci_move_to_fen(fen: str, uci: str) -> str:
    """
    Aplica un movimiento UCI simple a la FEN.
    Soporta:
    - movimientos normales
    - capturas
    - promociones
    - enroque por movimiento del rey
    No actualiza en-passant ni contadores con precisión de motor.
    Es suficiente para análisis táctico inicial.
    """
    parts = parse_fen_parts(fen)
    board_part, side_to_move, castling, ep_square, halfmove, fullmove = parts[:6]

    board = fen_piece_to_board_map(board_part)

    from_sq = square_to_index(uci[:2])
    to_sq = square_to_index(uci[2:4])
    promo = uci[4] if len(uci) == 5 else None

    moving_piece = board.get(from_sq)
    if moving_piece is None:
        raise ValueError(f"No hay pieza en {uci[:2]} para aplicar {uci}")

    piece_is_white = moving_piece.isupper()

    # En passant simplificado
    if moving_piece.lower() == "p" and ep_square != "-" and uci[2:4] == ep_square and to_sq not in board:
        ep_idx = square_to_index(ep_square)
        captured_sq = ep_idx - 8 if piece_is_white else ep_idx + 8
        board.pop(captured_sq, None)

    # Enroque simplificado
    if moving_piece.lower() == "k":
        if uci == "e1g1":
            board.pop(square_to_index("h1"), None)
            board[square_to_index("f1")] = "R"
        elif uci == "e1c1":
            board.pop(square_to_index("a1"), None)
            board[square_to_index("d1")] = "R"
        elif uci == "e8g8":
            board.pop(square_to_index("h8"), None)
            board[square_to_index("f8")] = "r"
        elif uci == "e8c8":
            board.pop(square_to_index("a8"), None)
            board[square_to_index("d8")] = "r"

    board.pop(from_sq, None)
    board.pop(to_sq, None)

    if promo is not None and moving_piece.lower() == "p":
        promoted = promo.upper() if piece_is_white else promo.lower()
        board[to_sq] = promoted
    else:
        board[to_sq] = moving_piece

    new_board_part = board_map_to_fen(board)

    # En-passant target simplificado
    new_ep = "-"
    if moving_piece.lower() == "p":
        from_rank = int(uci[1])
        to_rank = int(uci[3])
        if abs(to_rank - from_rank) == 2:
            mid_rank = (from_rank + to_rank) // 2
            new_ep = f"{uci[0]}{mid_rank}"

    # Castling rights simplificados
    new_castling = castling
    if moving_piece == "K":
        new_castling = new_castling.replace("K", "").replace("Q", "")
    elif moving_piece == "k":
        new_castling = new_castling.replace("k", "").replace("q", "")
    elif moving_piece == "R":
        if uci[:2] == "h1":
            new_castling = new_castling.replace("K", "")
        elif uci[:2] == "a1":
            new_castling = new_castling.replace("Q", "")
    elif moving_piece == "r":
        if uci[:2] == "h8":
            new_castling = new_castling.replace("k", "")
        elif uci[:2] == "a8":
            new_castling = new_castling.replace("q", "")

    if not new_castling:
        new_castling = "-"

    new_halfmove = "0" if moving_piece.lower() == "p" or to_sq in fen_piece_to_board_map(board_part) else str(int(halfmove) + 1)
    new_fullmove = str(int(fullmove) + 1) if side_to_move == "b" else fullmove

    return f"{new_board_part} {toggle_side(side_to_move)} {new_castling} {new_ep} {new_halfmove} {new_fullmove}"

def _describe_candidate_tactics(candidate: Dict[str, Any]) -> List[str]:
    messages: List[str] = []

    move = candidate.get("move", "?")
    tactics = candidate.get("tactics", {})
    side_to_move = tactics.get("side_to_move", "?")

    forks = tactics.get("forks", []) or []
    pins = tactics.get("pins", []) or []
    hanging = tactics.get("hanging_pieces", []) or []

    if forks:
        for fork in forks:
            attacker_piece = fork.get("attacker_piece", "piece")
            attacker_square = fork.get("attacker_square", "?")
            attacked_squares = ", ".join(fork.get("attacked_squares", []))
            messages.append(
                f"La jugada {move} deja disponible un fork para {side_to_move}: "
                f"{attacker_piece} desde {attacker_square} atacando {attacked_squares}."
            )

    if pins:
        for pin in pins:
            attacker_piece = pin.get("attacker_piece", "piece")
            attacker_square = pin.get("attacker_square", "?")
            pinned_piece = pin.get("pinned_piece", "piece")
            pinned_square = pin.get("pinned_square", "?")
            behind_piece = pin.get("behind_piece", "piece")
            behind_square = pin.get("behind_square", "?")
            messages.append(
                f"La jugada {move} permite una clavada para {side_to_move}: "
                f"{attacker_piece} en {attacker_square} clava {pinned_piece} en {pinned_square} "
                f"contra {behind_piece} en {behind_square}."
            )

    if hanging:
        for hp in hanging:
            piece = hp.get("piece", "piece")
            square = hp.get("square", "?")
            attacked_by = ", ".join(hp.get("attacked_by", []))
            messages.append(
                f"La jugada {move} deja una pieza colgando para {side_to_move}: "
                f"{piece} en {square}, atacada desde {attacked_by}."
            )

    return messages


def _build_pedagogical_summary(candidates: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
    total = summary.get("total", 0)
    forks = summary.get("forks", 0)
    pins = summary.get("pins", 0)
    hanging = summary.get("hanging_pieces", 0)

    if total == 0:
        headline = "No se detectaron temas tácticos inmediatos en las candidatas analizadas."
    else:
        headline = (
            f"Se detectaron {total} temas tácticos en las candidatas analizadas: "
            f"{forks} forks, {pins} pins y {hanging} piezas colgando."
        )

    detail_messages: List[str] = []
    best_warning: Optional[str] = None
    best_warning_score = -1

    for candidate in candidates:
        messages = _describe_candidate_tactics(candidate)
        detail_messages.extend(messages)

        candidate_summary = candidate.get("tactics", {}).get("summary", {})
        candidate_total = candidate_summary.get("total", 0)

        if candidate_total > best_warning_score and messages:
            best_warning_score = candidate_total
            best_warning = messages[0]

    return {
        "headline": headline,
        "details": detail_messages,
        "best_warning": best_warning,
    }


def analyze_tactical_candidates(
    fen: str,
    engine_path: str,
    depth: int = 3,
    multipv: int = 5,
) -> Dict[str, Any]:
    engine = StockfishUciEngine(engine_path)

    try:
        lines = engine.get_top_lines(fen=fen, depth=depth, multipv=multipv)

        candidates: List[Dict[str, Any]] = []
        fork_count = 0
        pin_count = 0
        hanging_count = 0

        for line in lines:
            if not line.pv:
                continue

            first_move = line.pv[0]
            try:
                resulting_fen = apply_uci_move_to_fen(fen, first_move)
                tactics = analyze_tactics(resulting_fen)
            except Exception as exc:
                candidates.append(
                    {
                        "move": first_move,
                        "error": str(exc),
                        "depth": line.depth,
                        "multipv": line.multipv,
                        "score_cp": line.score_cp,
                        "score_mate": line.score_mate,
                    }
                )
                continue

            summary = tactics["summary"]
            fork_count += summary["forks"]
            pin_count += summary["pins"]
            hanging_count += summary["hanging_pieces"]

            candidates.append(
                {
                    "move": first_move,
                    "depth": line.depth,
                    "multipv": line.multipv,
                    "score_cp": line.score_cp,
                    "score_mate": line.score_mate,
                    "pv": line.pv,
                    "resulting_fen": resulting_fen,
                    "tactics": tactics,
                }
            )

        summary = {
            "candidate_lines": len(candidates),
            "forks": fork_count,
            "pins": pin_count,
            "hanging_pieces": hanging_count,
            "total": fork_count + pin_count + hanging_count,
        }

        pedagogical_summary = _build_pedagogical_summary(candidates, summary)

        return {
            "input_fen": fen,
            "depth": depth,
            "multipv": multipv,
            "candidates": candidates,
            "summary": summary,
            "pedagogical_summary": pedagogical_summary,
        }


    finally:
        engine.stop()
