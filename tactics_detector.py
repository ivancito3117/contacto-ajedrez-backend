from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

PieceColor = str  # "white" | "black"
PieceType = str   # "pawn" | "knight" | "bishop" | "rook" | "queen" | "king"


PIECE_VALUES: Dict[PieceType, int] = {
    "pawn": 1,
    "knight": 3,
    "bishop": 3,
    "rook": 5,
    "queen": 9,
    "king": 100,
}


FILES = "abcdefgh"


@dataclass(frozen=True)
class Piece:
    color: PieceColor
    kind: PieceType


def square_name_to_index(square: str) -> int:
    file_idx = FILES.index(square[0])
    rank_idx = int(square[1]) - 1
    return rank_idx * 8 + file_idx


def index_to_square_name(index: int) -> str:
    file_idx = index % 8
    rank_idx = index // 8
    return f"{FILES[file_idx]}{rank_idx + 1}"


def on_board(file_idx: int, rank_idx: int) -> bool:
    return 0 <= file_idx < 8 and 0 <= rank_idx < 8


def index_to_coords(index: int) -> Tuple[int, int]:
    return index % 8, index // 8


def coords_to_index(file_idx: int, rank_idx: int) -> int:
    return rank_idx * 8 + file_idx


def fen_piece_to_piece(ch: str) -> Piece:
    color: PieceColor = "white" if ch.isupper() else "black"
    lower = ch.lower()
    kind_map: Dict[str, PieceType] = {
        "p": "pawn",
        "n": "knight",
        "b": "bishop",
        "r": "rook",
        "q": "queen",
        "k": "king",
    }
    return Piece(color=color, kind=kind_map[lower])


def parse_fen_board(fen: str) -> Dict[int, Piece]:
    board_part = fen.split()[0]
    rows = board_part.split("/")
    if len(rows) != 8:
        raise ValueError("FEN inválido: debe tener 8 filas")

    board: Dict[int, Piece] = {}
    rank = 7  # FEN empieza en la fila 8
    for row in rows:
        file_idx = 0
        for ch in row:
            if ch.isdigit():
                file_idx += int(ch)
            else:
                sq = coords_to_index(file_idx, rank)
                board[sq] = fen_piece_to_piece(ch)
                file_idx += 1
        rank -= 1

    return board


def get_side_to_move(fen: str) -> PieceColor:
    parts = fen.split()
    if len(parts) < 2:
        raise ValueError("FEN inválido: falta lado al mover")
    return "white" if parts[1] == "w" else "black"


def piece_symbol(piece: Piece) -> str:
    symbol_map = {
        "pawn": "P",
        "knight": "N",
        "bishop": "B",
        "rook": "R",
        "queen": "Q",
        "king": "K",
    }
    s = symbol_map[piece.kind]
    return s if piece.color == "white" else s.lower()


def squares_attacked_by_piece(board: Dict[int, Piece], square: int) -> Set[int]:
    piece = board.get(square)
    if piece is None:
        return set()

    file_idx, rank_idx = index_to_coords(square)
    attacks: Set[int] = set()

    if piece.kind == "pawn":
        dr = 1 if piece.color == "white" else -1
        for df in (-1, 1):
            nf, nr = file_idx + df, rank_idx + dr
            if on_board(nf, nr):
                attacks.add(coords_to_index(nf, nr))

    elif piece.kind == "knight":
        jumps = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ]
        for df, dr in jumps:
            nf, nr = file_idx + df, rank_idx + dr
            if on_board(nf, nr):
                attacks.add(coords_to_index(nf, nr))

    elif piece.kind == "king":
        for df in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if df == 0 and dr == 0:
                    continue
                nf, nr = file_idx + df, rank_idx + dr
                if on_board(nf, nr):
                    attacks.add(coords_to_index(nf, nr))

    elif piece.kind in {"bishop", "rook", "queen"}:
        directions: List[Tuple[int, int]] = []
        if piece.kind in {"bishop", "queen"}:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        if piece.kind in {"rook", "queen"}:
            directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])

        for df, dr in directions:
            nf, nr = file_idx + df, rank_idx + dr
            while on_board(nf, nr):
                target_sq = coords_to_index(nf, nr)
                attacks.add(target_sq)
                if target_sq in board:
                    break
                nf += df
                nr += dr

    return attacks


def attackers_of_square(
    board: Dict[int, Piece],
    target_square: int,
    by_color: PieceColor,
) -> List[int]:
    result: List[int] = []
    for sq, piece in board.items():
        if piece.color != by_color:
            continue
        if target_square in squares_attacked_by_piece(board, sq):
            result.append(sq)
    return result


def sliding_directions_for_piece(kind: PieceType) -> List[Tuple[int, int]]:
    if kind == "bishop":
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if kind == "rook":
        return [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if kind == "queen":
        return [
            (-1, -1), (-1, 1), (1, -1), (1, 1),
            (-1, 0), (1, 0), (0, -1), (0, 1),
        ]
    return []


def find_king_square(board: Dict[int, Piece], color: PieceColor) -> Optional[int]:
    for sq, piece in board.items():
        if piece.color == color and piece.kind == "king":
            return sq
    return None


def detect_forks(position: str) -> List[Dict[str, Any]]:
    """
    Detecta forks ya presentes en la posición.
    Un fork se reporta cuando una pieza ataca 2 o más piezas enemigas valiosas.
    """
    board = parse_fen_board(position)
    forks: List[Dict[str, Any]] = []

    for sq, piece in board.items():
        attacks = squares_attacked_by_piece(board, sq)
        attacked_enemy_squares: List[int] = []

        for target_sq in attacks:
            target_piece = board.get(target_sq)
            if target_piece is None:
                continue
            if target_piece.color == piece.color:
                continue
            if PIECE_VALUES[target_piece.kind] >= 3 or target_piece.kind == "king":
                attacked_enemy_squares.append(target_sq)

        if len(attacked_enemy_squares) >= 2:
            forks.append(
                {
                    "attacker_square": index_to_square_name(sq),
                    "attacker_piece": piece.kind,
                    "attacked_squares": [index_to_square_name(x) for x in attacked_enemy_squares],
                    "attacked_pieces": [board[x].kind for x in attacked_enemy_squares],
                    "color": piece.color,
                }
            )

    return forks


def detect_pins(position: str) -> List[Dict[str, Any]]:
    """
    Detecta pins geométricos:
    atacante deslizante -> pieza enemiga -> rey enemigo o pieza más valiosa detrás.
    """
    board = parse_fen_board(position)
    pins: List[Dict[str, Any]] = []

    for attacker_sq, attacker_piece in board.items():
        if attacker_piece.kind not in {"bishop", "rook", "queen"}:
            continue

        directions = sliding_directions_for_piece(attacker_piece.kind)
        af, ar = index_to_coords(attacker_sq)

        for df, dr in directions:
            nf, nr = af + df, ar + dr
            first_blocker_sq: Optional[int] = None

            while on_board(nf, nr):
                sq = coords_to_index(nf, nr)
                if sq in board:
                    if first_blocker_sq is None:
                        first_blocker_sq = sq
                    else:
                        first_piece = board[first_blocker_sq]
                        second_piece = board[sq]

                        if first_piece.color != attacker_piece.color and second_piece.color != attacker_piece.color:
                            if second_piece.kind == "king" or PIECE_VALUES[second_piece.kind] > PIECE_VALUES[first_piece.kind]:
                                pins.append(
                                    {
                                        "attacker_square": index_to_square_name(attacker_sq),
                                        "attacker_piece": attacker_piece.kind,
                                        "pinned_square": index_to_square_name(first_blocker_sq),
                                        "pinned_piece": first_piece.kind,
                                        "behind_square": index_to_square_name(sq),
                                        "behind_piece": second_piece.kind,
                                        "color": attacker_piece.color,
                                    }
                                )
                        break
                nf += df
                nr += dr

    return pins


def detect_hanging_pieces(position: str) -> List[Dict[str, Any]]:
    """
    Detecta piezas colgando:
    piezas atacadas por el rival y no defendidas por su propio bando.
    """
    board = parse_fen_board(position)
    hanging: List[Dict[str, Any]] = []

    for sq, piece in board.items():
        enemy_color: PieceColor = "black" if piece.color == "white" else "white"

        attackers = attackers_of_square(board, sq, enemy_color)
        defenders = attackers_of_square(board, sq, piece.color)

        # Quitar la pieza misma de sus "defensores" si por la geometría aparece incluida
        defenders = [d for d in defenders if d != sq]

        if attackers and not defenders:
            hanging.append(
                {
                    "square": index_to_square_name(sq),
                    "piece": piece.kind,
                    "color": piece.color,
                    "attacked_by": [index_to_square_name(a) for a in attackers],
                    "attacker_pieces": [board[a].kind for a in attackers],
                }
            )

    return hanging


def analyze_tactics(position: str) -> Dict[str, Any]:
    forks = detect_forks(position)
    pins = detect_pins(position)
    hanging = detect_hanging_pieces(position)

    return {
        "side_to_move": get_side_to_move(position),
        "forks": forks,
        "pins": pins,
        "hanging_pieces": hanging,
        "summary": {
            "forks": len(forks),
            "pins": len(pins),
            "hanging_pieces": len(hanging),
            "total": len(forks) + len(pins) + len(hanging),
        },
    }
