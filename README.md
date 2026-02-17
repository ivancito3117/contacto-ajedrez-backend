# Plataforma Ajedrez Iván ♟️🚦

Backend educativo basado en **FastAPI + SQLAlchemy** que integra datos reales de **Lichess** para gestionar estudiantes, sincronizar partidas y generar un **reporte pedagógico** con **semáforos (traffic lights)** explicables.

---

## ✨ Características principales

- ✅ API REST con FastAPI
- 👥 Gestión de estudiantes (CRUD básico)
- 🌐 Consulta de perfil en Lichess (token opcional)
- ♟️ Descarga de partidas desde Lichess en formato **NDJSON**
- 💾 Sincronización y almacenamiento local de partidas (DB)
- 📊 Reporte pedagógico por estudiante:
  - Actividad (últimos 7 días, última partida, frecuencia estimada)
  - Rendimiento (victorias, derrotas, empates, win rate)
  - Perfil (ritmos, modalidades, aperturas frecuentes)
- 🚦 Semáforos pedagógicos generados por `build_traffic_lights(activity, performance)`

---

## 🧱 Estructura del proyecto

> Estructura base detectada en la carpeta del proyecto:

- `main.py` — API principal (endpoints, integración Lichess, reporte pedagógico)
- `db.py` — conexión a base de datos, `Base`, `engine`, `get_db`
- `models.py` — modelos ORM (`Student`, `Game`)
- `schemas.py` — esquemas Pydantic (`StudentCreate`, `StudentOut`)
- `traffic_lights.py` — lógica de semáforos pedagógicos
- `docs/` — documentación del proyecto (en construcción)
- `venv/` — entorno virtual local

---

## ⚙️ Requisitos

- Python 3.10+ recomendado
- Entorno virtual (`venv`)
- Base de datos (según configuración en `db.py`)
  - Se ve instalado `psycopg2-binary`, así que suele ser **PostgreSQL**
- Token de Lichess (opcional pero recomendado)

---

## 🔐 Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
LICHESS_TOKEN=tu_token_de_lichess_aqui
