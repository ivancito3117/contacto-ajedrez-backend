from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import requests
import json

from db import Base, engine, get_db
from models import Student, Game
from schemas import StudentCreate, StudentOut
from traffic_lights import build_traffic_lights


load_dotenv()
LICHESS_TOKEN = os.getenv("LICHESS_TOKEN")

app = FastAPI(title="Plataforma Ajedrez Iván")

# Crea tablas (simple para MVP; luego migramos con Alembic)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"estado": "Servidor activo", "autor": "Iván"}

@app.get("/lichess/perfil")
def lichess_profile():
    if not LICHESS_TOKEN:
        raise HTTPException(status_code=500, detail="LICHESS_TOKEN no configurado")

    r = requests.get(
        "https://lichess.org/api/account",
        headers={"Authorization": f"Bearer {LICHESS_TOKEN}"}
    )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

# ---------- ESTUDIANTES ----------
@app.post("/students", response_model=StudentOut)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    exists = db.query(Student).filter(Student.lichess_username == payload.lichess_username).first()
    if exists:
        raise HTTPException(status_code=409, detail="Ese lichess_username ya está registrado")

    s = Student(
        full_name=payload.full_name,
        level=payload.level,
        grade=payload.grade,
        lichess_username=payload.lichess_username
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.get("/students", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.id.desc()).all()

@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return s

# ---------- PARTIDAS DESDE LICHESS (NDJSON) ----------
def _parse_ndjson(text: str) -> list[dict]:
    games = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        games.append(json.loads(line))
    return games

@app.get("/students/{student_id}/lichess/games")
def student_lichess_games(
    student_id: int,
    max_games: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Lichess export user games (normalmente entrega NDJSON si se pide en Accept)
    url = f"https://lichess.org/api/games/user/{s.lichess_username}"
    headers = {"Accept": "application/x-ndjson"}
    # Si tienes token, ayuda a estabilidad/limitación
    if LICHESS_TOKEN:
        headers["Authorization"] = f"Bearer {LICHESS_TOKEN}"

    params = {
        "max": max_games,
        "moves": "true",
        "clocks": "true",
        "opening": "true",
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if r.status_code == 429:
        # Regla oficial: esperar un minuto si 429 :contentReference[oaicite:1]{index=1}
        raise HTTPException(status_code=429, detail="Rate limit Lichess (429). Espera 60s y reintenta.")
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    # Intentamos NDJSON; si Lichess responde PGN por alguna razón, lo devolvemos como texto.
    ct = (r.headers.get("content-type") or "").lower()
    if "ndjson" in ct:
        return {"format": "ndjson", "games": _parse_ndjson(r.text)}
    else:
        return {"format": "pgn", "pgn": r.text}

from datetime import datetime, timezone

def _ms_to_dt(ms: int | None):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

def _safe_get(d: dict, path: list[str]):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

@app.post("/students/{student_id}/lichess/sync")
def sync_student_games(
    student_id: int,
    max_games: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    url = f"https://lichess.org/api/games/user/{s.lichess_username}"
    headers = {"Accept": "application/x-ndjson"}
    if LICHESS_TOKEN:
        headers["Authorization"] = f"Bearer {LICHESS_TOKEN}"

    params = {
        "max": max_games,
        "moves": "true",
        "clocks": "true",
        "opening": "true",
        "pgnInJson": "true",   # suele incluir PGN dentro del JSON cuando es NDJSON
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if r.status_code == 429:
        raise HTTPException(status_code=429, detail="Rate limit Lichess (429). Espera 60s y reintenta.")
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    ct = (r.headers.get("content-type") or "").lower()
    if "ndjson" not in ct:
        raise HTTPException(status_code=500, detail="No recibí NDJSON; revisa parámetros/headers.")

    games = _parse_ndjson(r.text)

    inserted = 0
    skipped = 0

    for g in games:
        gid = g.get("id")
        if not gid:
            continue

        exists = db.query(Game).filter(
            Game.student_id == s.id,
            Game.lichess_game_id == gid
        ).first()
        if exists:
            skipped += 1
            continue

        played_at = _ms_to_dt(g.get("createdAt") or g.get("lastMoveAt"))
        speed = g.get("speed")
        perf = _safe_get(g, ["perf", "name"]) or g.get("perf")
        pgn = g.get("pgn")

        row = Game(
            student_id=s.id,
            lichess_game_id=gid,
            played_at=played_at,
            speed=speed,
            perf=str(perf) if perf is not None else None,
            pgn=pgn,
            json_raw=json.dumps(g)
        )
        db.add(row)
        inserted += 1

    db.commit()

    return {
        "student_id": s.id,
        "lichess_username": s.lichess_username,
        "requested": len(games),
        "inserted": inserted,
        "skipped_existing": skipped
    }

@app.get("/students/{student_id}/games")
def list_games_from_db(
    student_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    rows = (db.query(Game)
            .filter(Game.student_id == s.id)
            .order_by(Game.played_at.desc().nullslast(), Game.id.desc())
            .limit(limit)
            .all())

    return {
        "student_id": s.id,
        "count": len(rows),
        "games": [
            {
                "lichess_game_id": x.lichess_game_id,
                "played_at": x.played_at,
                "speed": x.speed,
                "perf": x.perf
            } for x in rows
        ]
    }

from collections import Counter
from datetime import datetime, timezone, timedelta

def _dt_now_utc():
    return datetime.now(timezone.utc)

def _parse_game_row(row: Game) -> dict | None:
    """Devuelve un dict del juego a partir de json_raw; si está dañado, None."""
    if not row.json_raw:
        return None
    try:
        return json.loads(row.json_raw)
    except Exception:
        return None

def _game_result_for_username(g: dict, username: str) -> str:
    """
    Intenta deducir win/loss/draw/unknown para el username.
    Funciona si el NDJSON trae 'players' + 'winner' o 'status'.
    """
    username_l = username.lower()

    players = g.get("players") or {}
    white = (players.get("white") or {}).get("user") or {}
    black = (players.get("black") or {}).get("user") or {}

    white_name = (white.get("name") or "").lower()
    black_name = (black.get("name") or "").lower()

    winner = g.get("winner")  # 'white' o 'black' a veces
    status = g.get("status")  # 'draw', 'resign', 'mate', etc.

    # Si hay status draw explícito
    if status == "draw":
        return "draw"

    # Si hay winner, ubicamos el color del usuario
    if winner in ("white", "black"):
        if white_name == username_l:
            return "win" if winner == "white" else "loss"
        if black_name == username_l:
            return "win" if winner == "black" else "loss"

    # Si no hay info suficiente
    return "unknown"

def _opening_name(g: dict) -> str | None:
    opening = g.get("opening")
    if isinstance(opening, dict):
        name = opening.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None

@app.get("/students/{student_id}/report")
def student_pedagogical_report(
    student_id: int,
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    since = _dt_now_utc() - timedelta(days=days)
    since_7 = _dt_now_utc() - timedelta(days=7)

    # Contadores "baratos" sin traer todo
    last_7 = (
        db.query(Game)
        .filter(
            Game.student_id == s.id,
            Game.played_at != None,   # noqa: E711
            Game.played_at >= since_7,
        )
        .count()
    )

    last_played = (
        db.query(Game.played_at)
        .filter(
            Game.student_id == s.id,
            Game.played_at != None,   # noqa: E711
        )
        .order_by(Game.played_at.desc())
        .limit(1)
        .scalar()
    )

    # Traemos SOLO juegos dentro de ventana (y con límite)
    MAX_GAMES = 2000
    rows = (
        db.query(Game)
        .filter(
            Game.student_id == s.id,
            Game.played_at != None,   # noqa: E711
            Game.played_at >= since,
        )
        .order_by(Game.played_at.desc(), Game.id.desc())
        .limit(MAX_GAMES)
        .all()
    )

    # Procesamos
    in_window = 0
    res_counter = Counter()
    speed_counter = Counter()
    perf_counter = Counter()
    opening_counter = Counter()

    for row in rows:
        g = _parse_game_row(row)
        in_window += 1

        # Resultado
        result = _game_result_for_username(g, s.lichess_username) if g else "unknown"
        res_counter[result] += 1

        # Ritmo / perf
        if row.speed:
            speed_counter[row.speed] += 1
        if row.perf:
            perf_counter[row.perf] += 1

        # Aperturas
        if g:
            op = _opening_name(g)
            if op:
                opening_counter[op] += 1

    wins = res_counter["win"]
    losses = res_counter["loss"]
    draws = res_counter["draw"]
    known = wins + losses + draws
    effectiveness = (wins / known) if known else 0.0

    top_speeds = [k for k, _ in speed_counter.most_common(3)]
    top_perfs = [k for k, _ in perf_counter.most_common(3)]
    top_openings = [k for k, _ in opening_counter.most_common(5)]

    # Partidas/semana estimado (en ventana "days")
    per_week = (in_window / max(days, 1)) * 7.0

    report = {
        "student": {
            "id": s.id,
            "name": s.full_name,
            "level": s.level,
            "grade": s.grade,
            "lichess_username": s.lichess_username,
        },
        "activity": {
            "days_window": days,
            "games_in_window": in_window,
            "games_last_7_days": last_7,
            "games_per_week_estimated": round(per_week, 2),
            "last_played_at": last_played,
        },
        "performance": {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "known_results": known,
            "win_rate_percent": round(effectiveness * 100.0, 1),
        },
        "profile": {
            "top_speeds": top_speeds,
            "top_perfs": top_perfs,
            "top_openings": top_openings,
        },
    }

    # 👉 calcular days_since_last_game
    days_since_last_game = None
    if last_played:
        days_since_last_game = (_dt_now_utc() - last_played).days

    # 👉 inyectar campos que esperan los semáforos
    report["activity"]["days_since_last_game"] = days_since_last_game
    report["activity"]["games_last_7d"] = last_7

    # 👉 construir semáforos pedagógicos
    activity = report.get("activity") or {}
    performance = report.get("performance") or {}

    report["traffic_lights"] = build_traffic_lights(activity, performance)

    return report
    
    # ===============================
# SYSTEM DOCS ENDPOINT
# ===============================

import pathlib

@app.get("/system/docs")
def system_docs():
    """
    Endpoint de autodescripción del sistema.
    Permite que cualquier IA o desarrollador entienda la arquitectura del backend.
    """

    base = pathlib.Path(__file__).parent

    docs = {}
    docs_path = base / "docs"

    if docs_path.exists():
        for file in docs_path.glob("*.md"):
            try:
                docs[file.name] = file.read_text(encoding="utf-8")[:2000]
            except Exception:
                docs[file.name] = "No se pudo leer"

    return {
        "system": "Contacto Ajedrez Backend",
        "version": "1.0",
        "author": "Iván",
        "description": "Backend pedagógico de análisis ajedrecístico",
        "stack": [
            "FastAPI",
            "SQLAlchemy",
            "PostgreSQL",
            "Pydantic"
        ],
        "main_modules": [
            "main.py → API endpoints",
            "models.py → ORM models",
            "schemas.py → validation schemas",
            "db.py → database config",
            "traffic_lights.py → pedagogical engine"
        ],
        "docs": docs
    }

