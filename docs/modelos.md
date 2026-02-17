# Modelos de Datos — Plataforma Ajedrez Iván

Este módulo define la estructura de base de datos usando SQLAlchemy ORM.

---

## Tabla: students

Representa los estudiantes registrados en el sistema.

| Campo | Tipo | Descripción |
|------|-----|-------------|
id | Integer | Identificador único |
full_name | String(120) | Nombre completo |
level | String(20) | Nivel educativo (primaria/bachillerato) |
grade | String(20) | Grado académico |
lichess_username | String(60) | Usuario Lichess |
created_at | DateTime | Fecha de creación |

### Restricciones

- `lichess_username` es único
- no se permiten estudiantes duplicados con mismo usuario

---

## Tabla: games

Representa partidas sincronizadas desde Lichess.

| Campo | Tipo | Descripción |
|------|-----|-------------|
id | Integer | Identificador interno |
student_id | Integer | FK hacia estudiante |
lichess_game_id | String(32) | ID de partida en Lichess |
played_at | DateTime | Fecha de la partida |
speed | String(20) | Ritmo (blitz, rapid, etc.) |
perf | String(30) | Categoría Lichess |
result | String(20) | Resultado pedagógico |
pgn | Text | PGN opcional |
json_raw | Text | Datos originales NDJSON |
created_at | DateTime | Fecha registro |

---

## Relaciones

# Student 1 ──── N Game


# Un estudiante puede tener múltiples partidas.

---

## Restricciones de integridad

- combinación `(student_id, lichess_game_id)` es única
- evita duplicar partidas sincronizadas

---

## Eliminación en cascada

# Si se elimina un estudiante:

# ON DELETE CASCADE


→ se eliminan automáticamente todas sus partidas.

---

## Decisiones de diseño

Se guarda:

- PGN → para análisis futuro
- JSON crudo → para recalcular métricas sin reconsultar API

Esto convierte la base de datos en un **repositorio histórico analítico**.

---

## Flujo lógico

Lichess API → Sync endpoint → Parse NDJSON → Insert DB → Reporte pedagógico

---

## Conclusión técnica

El diseño de modelos es escalable, normalizado y preparado para análisis pedagógico avanzado, manteniendo consistencia, integridad referencial y eficiencia de consulta.




