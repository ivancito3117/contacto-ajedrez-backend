# Semáforos Pedagógicos — Plataforma Ajedrez Iván 🚦♟️

Este módulo define un sistema de **juicios pedagógicos explicables** (traffic lights) construido con reglas claras y mensajes interpretables para docentes y estudiantes.

El objetivo es traducir datos de juego (actividad y rendimiento) en un estado simple:

- 🟢 Verde: estable / encaminado
- 🟡 Amarillo: en observación
- 🔴 Rojo: requiere atención

---

## Estructura del resultado

La función principal devuelve:

```json
{
  "activity": "green|yellow|red",
  "performance": "green|yellow|red",
  "stability": "green|yellow|red",
  "messages": ["..."]
}

* activity: hábitos de juego (frecuencia/recencia)
* performance: efectividad (win rate)
* stability: lectura institucional combinada
* messages: explicación humana (lo que aparece en “Ver razones”)

1) Semáforo de Actividad (activity_light)

# Entradas

* days_since_last_game (int | None)

* games_last_7d (int)

Reglas base

🟢 Verde

* jugó hace ≤ 3 días

* y tuvo ≥ 5 partidas en 7 días

🟡 Amarillo

* jugó hace 4 a 10 días, o

* tuvo < 5 partidas en 7 días

🔴 Rojo

* ≥ 11 días sin jugar (inactividad clara)

# Manejo de falta de datos

Si days_since_last_game es None:

* devuelve 🟡 amarillo
* mensaje: “pendiente de sincronización”

# Mensajes explicables

# El módulo genera mensajes como:

* “Inactividad: X días sin jugar.”
* “Bajo volumen reciente: N/7 días (meta: 5).”
* “Alta constancia de juego.”

2) Semáforo de Rendimiento (performance_light)

# Entrada

* win_rate_percent (float | None)

# Reglas base

* 🟢 Verde: >= 50%
* 🟡 Amarillo: 35% - 49%
* 🔴 Rojo: < 35%

# Manejo de falta de datos

Si win_rate_percent es None:

* devuelve 🟡 amarillo
* mensaje: “faltan partidas suficientes”

# Mensajes típicos

* “Efectividad sólida: winrate X%.”
* “Efectividad moderada: se recomienda seguimiento.”
* “Efectividad baja: conviene intervención del tutor.”

3) Semáforo de Estabilidad (stability_light)

# Este es el semáforo institucional/pedagógico: combina actividad y rendimiento.

# Regla simple y explicable

* 🔴 si actividad o rendimiento están en rojo
* 🟢 si ambos están en verde
* 🟡 en cualquier otro caso (señales mixtas)

# Matices pedagógicos (mensajes)

# Cuando hay rojo, el sistema diferencia escenarios:

* Constante pero frustrado:
	* actividad 🟢 y rendimiento 🔴
* Abandono silencioso:
	* actividad 🔴 y rendimiento 🟢/🟡
* Riesgo general:
	* ambos críticos o señales fuertes

Función principal (build_traffic_lights)

# Entradas esperadas

* activity:
	* days_since_last_game
	* games_last_7d
* performance:
	* win_rate_percent
	
# Ejemplo:

{
  "activity": {"days_since_last_game": 6, "games_last_7d": 2},
  "performance": {"win_rate_percent": 42.5}
}

* Orden de mensajes (UX docente)

	* Los mensajes se ordenan así:
		* estabilidad (lectura institucional)
		* actividad (hábitos)
		* rendimiento (efectividad)

* Esto hace que el usuario entienda primero “el diagnóstico general” y luego “las razones”.

Ventajas del enfoque

✔ Explicable (reglas claras)

✔ Ajustable (parámetros configurables)

✔ Pedagógico (mensajes orientados a tutoría)

✔ Escalable (se pueden añadir más métricas sin romper API)

✔ Compatible con UI (modal “Ver razones”)

# Posibles extensiones futuras

* Semáforo de táctica (errores graves por partida)
* Semáforo de aperturas (repertorio y diversidad)
* Semáforo de estabilidad emocional (rachas de derrotas)
* Personalización por nivel (primaria vs bachillerato)

# Conclusión

# traffic_lights.py implementa un sistema de evaluación pedagógica simple pero potente: convierte métricas de juego en señales visuales interpretables, con explicaciones claras que facilitan intervención educativa oportuna.


