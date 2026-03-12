# Contacto Ajedrez

**Autor:** Iván  

Contacto Ajedrez es una plataforma pedagógica de ajedrez que combina análisis automático, seguimiento de estudiantes y exploración de patrones tácticos utilizando herramientas modernas de desarrollo de software.

El sistema integra motores de análisis, bases de datos de partidas y una interfaz interactiva para apoyar procesos de enseñanza y aprendizaje del ajedrez.

---

# Arquitectura del sistema

El proyecto está compuesto por dos grandes componentes:

### Backend
Desarrollado en **Python con FastAPI**, encargado de:

- gestión de estudiantes
- sincronización con Lichess
- análisis táctico con Stockfish
- detección automática de patrones
- ejecución de consultas CQL
- generación de reportes pedagógicos
- transmisión de partidas en vivo mediante WebSockets

### Frontend
Aplicación desarrollada en **Flutter** que permite:

- visualización de partidas
- análisis táctico interactivo
- panel de tutor
- laboratorio de patrones CQL
- seguimiento pedagógico mediante semáforos de rendimiento

---

# Tecnologías utilizadas

## Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Stockfish 18
- CQL (Chess Query Language)

## Frontend

- Flutter
- Riverpod
- SharedPreferences
- API client personalizado

---

# Funcionalidades principales

### Gestión de estudiantes

Endpoints:

/students
/students/{id}
/students/{id}/report


Permite gestionar estudiantes y generar reportes pedagógicos basados en su actividad y rendimiento.

---

### Sincronización con Lichess

/students/{id}/lichess/sync
/students/{id}/lichess/games


Importa partidas públicas desde Lichess para análisis.

---

### Análisis táctico automático

POST /analyze/tactics


Pipeline de análisis:

Stockfish → tactical_search.py → tactics_detector.py


Detecta patrones como:

- forks
- pins
- piezas colgantes

---

### Semáforos pedagógicos

Sistema de evaluación automática que clasifica el desempeño del estudiante en:

- actividad
- rendimiento
- estabilidad

Representado mediante estados:

- 🟢 bueno
- 🟡 atención
- 🔴 riesgo

---

### Partidas en vivo

/ws/games/{game_id}


Implementado mediante **WebSockets**, permite visualizar partidas en tiempo real desde la aplicación.

---

### Laboratorio CQL

/cql/run-pattern


Permite ejecutar consultas de **Chess Query Language** para detectar patrones específicos dentro de bases de datos de partidas.

---

# Estructura del proyecto

├── main.py
├── models.py
├── schemas.py
├── db.py
├── live_api.py
├── live_ws.py
├── tactical_search.py
├── tactics_detector.py
├── traffic_lights.py
├── cql_runner.py
├── chessdb/
├── cql/
├── engines/
├── docs/
└── scripts/


---

# Objetivo del proyecto

El objetivo de **Contacto Ajedrez** es construir una plataforma que permita:

- analizar automáticamente partidas de ajedrez
- detectar patrones tácticos
- generar retroalimentación pedagógica
- apoyar el entrenamiento sistemático de estudiantes
- integrar herramientas modernas de análisis y visualización.

---

# Estado del proyecto

El backend se encuentra actualmente operativo con:

- gestión de estudiantes
- sincronización con Lichess
- análisis táctico
- laboratorio CQL
- partidas en vivo

El siguiente paso de desarrollo contempla:

- autenticación de usuarios
- control de acceso por roles (tutor / estudiante)
- tablero personal para estudiantes
- mejoras pedagógicas en los reportes automáticos.


