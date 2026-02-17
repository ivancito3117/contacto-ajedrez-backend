# Base de Datos — Plataforma Ajedrez Iván

Este módulo define la conexión a base de datos y el manejo de sesiones usando SQLAlchemy.

---

## Configuración

La conexión se obtiene desde variable de entorno:

`DATABASE_URL`

Si no está definida, el sistema se detiene con error:

RuntimeError("DATABASE_URL no está configurado en .env")


Esto asegura que la aplicación nunca corra sin conexión válida.

---

## Motor de base de datos

```python
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# pool_pre_ping=True

Permite verificar que la conexión siga viva antes de usarla.

Evita errores cuando:

la DB se reinicia

la conexión queda inactiva

hay timeouts de red

# Sesiones

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

| Configuración    | Motivo                       |
| ---------------- | ---------------------------- |
| autocommit=False | Control manual de commits    |
| autoflush=False  | Evita escrituras inesperadas |
| bind=engine      | Sesión conectada al motor    |

# Base declarativa

Base = declarative_base()

# Todos los modelos ORM heredan de esta base.

def get_db():

# Dependency Injection (FastAPI)

# Función:

def get_db():

# Se usa en endpoints así:

db: Session = Depends(get_db)

# Comportamiento

# abre sesión

# la entrega al endpoint

# la cierra automáticamente

# Garantiza:

# no fugas de conexión

# manejo seguro

# limpieza automática

# Flujo interno

Request → FastAPI → Depends(get_db) → Session → Query → Response → Close

Buenas prácticas implementadas

✔ Manejo seguro de sesiones
✔ Configuración externa por variables de entorno
✔ Pool con verificación automática
✔ Arquitectura desacoplada

# Futuras mejoras recomendadas

# Migraciones con Alembic

# Pool tuning para producción

# Logging SQL opcional

# Retry automático en fallos transitorios

# Conclusión técnica

# El módulo db.py implementa correctamente el patrón estándar de conexión a base de datos para aplicaciones FastAPI productivas, garantizando estabilidad, escalabilidad y mantenimiento limpio.

