from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CQL_DIR = BASE_DIR / "cql"
CHESSDB_DIR = BASE_DIR / "chessdb"
RESULTS_DIR = CHESSDB_DIR / "results"

CQL_BIN = CQL_DIR / "cql"
DEFAULT_DB = CHESSDB_DIR / "hhdbvi_clean.pgn"


def _safe_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_") or "query"


def run_cql_query(query_file: str, db_file: str | None = None, timeout: int = 120) -> dict:
    """
    Ejecuta CQL sobre una base PGN saneada.
    query_file: ruta relativa dentro de cql/, por ejemplo 'exalpha/greekgift.cql'
    db_file: ruta absoluta o None para usar hhdbvi_clean.pgn
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    query_path = (CQL_DIR / query_file).resolve()
    if not query_path.exists():
        raise FileNotFoundError(f"No existe query_file: {query_path}")

    db_path = Path(db_file).resolve() if db_file else DEFAULT_DB.resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"No existe db_file: {db_path}")

    query_stem = _safe_name(query_path.stem)
    output_path = RESULTS_DIR / f"{query_stem}-out.pgn"

    cmd = [
        str(CQL_BIN),
        "-input",
        str(db_path),
        str(query_path),
    ]

    started = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=str(CQL_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = round(time.perf_counter() - started, 3)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    matches = None
    m = re.search(r"(\d+)\s+matches\s+of\s+(\d+)\s+games", stdout)
    total_games = None
    if m:
        matches = int(m.group(1))
        total_games = int(m.group(2))

    return {
        "ok": result.returncode == 0,
        "command": cmd,
        "query_file": str(query_path),
        "db_file": str(db_path),
        "output_file": str(output_path),
        "elapsed_seconds": elapsed,
        "matches": matches,
        "total_games": total_games,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": result.returncode,
    }

def list_cql_examples() -> dict:
    """
    Lista los archivos .cql disponibles en exalpha/ y queries/.
    """
    exalpha_dir = CQL_DIR / "exalpha"
    queries_dir = CQL_DIR / "queries"

    exalpha = sorted(
        [f"exalpha/{p.name}" for p in exalpha_dir.glob("*.cql")]
    ) if exalpha_dir.exists() else []

    queries = sorted(
        [f"queries/{p.name}" for p in queries_dir.glob("*.cql")]
    ) if queries_dir.exists() else []

    return {
        "exalpha": exalpha,
        "queries": queries,
        "total": len(exalpha) + len(queries),
    }
