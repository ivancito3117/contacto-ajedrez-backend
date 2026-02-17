# Schemas API — Plataforma Ajedrez Iván

Este módulo define los modelos de validación de datos usando **Pydantic**.  
Los schemas controlan qué datos entran y salen del sistema.

---

## StudentCreate

Schema usado para crear estudiantes.

```json
POST /students

| Campo            | Tipo   | Reglas                           |
| ---------------- | ------ | -------------------------------- |
| full_name        | string | 3–120 caracteres                 |
| level            | string | solo "primaria" o "bachillerato" |
| grade            | string | opcional, máx 20                 |
| lichess_username | string | 2–60 caracteres                  |

# Validaciones clave

* full_name tiene longitud mínima

* level usa regex para restringir valores válidos

* grade es opcional

* lichess_username tiene longitud controlada

# Estas validaciones evitan datos inválidos antes de llegar a la base de datos.

# StudentOut

# Schema de salida usado en respuestas API.

# Se usa en endpoints:

* GET /students

* GET /students/{id}

* POST /students

| Campo            | Tipo        |
| ---------------- | ----------- |
| id               | int         |
| full_name        | string      |
| level            | string      |
| grade            | string/null |
| lichess_username | string      |

# Configuración ORM

class Config:
    from_attributes = True

# Permite convertir automáticamente objetos SQLAlchemy a JSON sin mapeos manuales.

# Esto habilita:

ORM object → Schema → JSON response

# Flujo de datos

Cliente → JSON → Schema entrada → Endpoint → DB → Schema salida → JSON → Cliente

# Buenas prácticas implementadas

✔ Validación fuerte de datos
✔ Restricciones de longitud
✔ Restricciones de dominio (regex)
✔ Separación input/output schemas
✔ Compatibilidad ORM automática

# Beneficio arquitectónico

# Los schemas desacoplan:

* base de datos

* lógica de negocio

* API externa

# Esto permite modificar la base de datos sin romper la API.

# Conclusión técnica

# El módulo schemas.py implementa correctamente la capa de validación y serialización, garantizando integridad de datos, seguridad de entrada y consistencia en respuestas API.

