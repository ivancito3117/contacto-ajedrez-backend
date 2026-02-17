from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


Color = Literal["green", "yellow", "red"]


@dataclass
class TrafficLightsResult:
    activity: Color
    performance: Color
    stability: Color
    messages: List[str]


def _color_rank(c: Color) -> int:
    # mientras más alto, peor
    return {"green": 0, "yellow": 1, "red": 2}[c]


def activity_light(
    days_since_last_game: Optional[int],
    games_last_7d: int,
    *,
    green_max_days: int = 3,
    green_min_games_7d: int = 5,
    yellow_max_days: int = 10,
    red_min_days: int = 11,
) -> tuple[Color, List[str]]:
    """
    Reglas (tal cual tu diseño base):
    🟢 si jugó en <=3 días y >=5 partidas en 7 días
    🟡 si 4-10 días sin jugar o <5 partidas en 7 días
    🔴 si >10-14 días sin jugar (aquí usamos >=11 como rojo inicial)
    """
    msgs: List[str] = []

    # Sin datos => tratamos como amarillo con mensaje
    if days_since_last_game is None:
        return "yellow", ["Sin registro de última partida aún (pendiente de sincronización)."]

    if days_since_last_game >= red_min_days:
        msgs.append(f"Inactividad: {days_since_last_game} días sin jugar.")
        return "red", msgs

    # verde exige ambas condiciones
    if days_since_last_game <= green_max_days and games_last_7d >= green_min_games_7d:
        msgs.append("Alta constancia de juego.")
        msgs.append(f"{games_last_7d} partidas en los últimos 7 días.")
        return "green", msgs

    # amarillo por intermitencia
    if 4 <= days_since_last_game <= yellow_max_days:
        msgs.append(f"Intermitente: {days_since_last_game} días sin jugar.")
    if games_last_7d < green_min_games_7d:
        msgs.append(f"Bajo volumen reciente: {games_last_7d}/7 días (meta: {green_min_games_7d}).")

    # si no se agregó nada, igual definimos un mensaje suave
    if not msgs:
        msgs.append("Actividad moderada.")

    return "yellow", msgs


def performance_light(
    win_rate_percent: Optional[float],
    *,
    green_min: float = 50.0,
    yellow_min: float = 35.0,
) -> tuple[Color, List[str]]:
    """
    Reglas base:
    🟢 >= 50%
    🟡 35% - 49%
    🔴 < 35%
    """
    msgs: List[str] = []
    if win_rate_percent is None:
        return "yellow", ["Sin datos de rendimiento todavía (faltan partidas suficientes)."]

    wr = float(win_rate_percent)

    if wr >= green_min:
        msgs.append(f"Efectividad sólida: winrate {wr:.0f}%.")
        return "green", msgs

    if yellow_min <= wr < green_min:
        msgs.append(f"Efectividad moderada: winrate {wr:.0f}%.")
        msgs.append("Se recomienda seguimiento pedagógico.")
        return "yellow", msgs

    msgs.append(f"Efectividad baja: winrate {wr:.0f}%.")
    msgs.append("Posible frustración o bloqueo técnico: conviene intervención del tutor.")
    return "red", msgs


def stability_light(activity: Color, performance: Color) -> tuple[Color, List[str]]:
    """
    Interpretación institucional (tu idea):
    - Verde: bien encaminado / estable
    - Amarillo: en observación
    - Rojo: requiere atención

    Regla simple y explicable:
    - Si alguno es rojo => estabilidad rojo
    - Si ambos verdes => verde
    - En otro caso => amarillo
    """
    msgs: List[str] = []

    if activity == "red" or performance == "red":
        # matices útiles
        if activity == "green" and performance == "red":
            msgs.append("Constante pero frustrado: juega mucho y los resultados no acompañan.")
        elif activity == "red" and performance in ("green", "yellow"):
            msgs.append("Abandono silencioso: bajó la actividad aunque el rendimiento no sea crítico.")
        else:
            msgs.append("Requiere atención: hay señales fuertes de riesgo.")
        return "red", msgs

    if activity == "green" and performance == "green":
        msgs.append("Estable: buen hábito y buen rendimiento.")
        return "green", msgs

    msgs.append("En observación: señales mixtas (hábito y rendimiento no están alineados).")
    return "yellow", msgs


def build_traffic_lights(activity: Dict[str, Any], performance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Espera que 'activity' y 'performance' vengan del reporte actual.
    Campos mínimos recomendados:
      activity: { "days_since_last_game": int|None, "games_last_7d": int }
      performance: { "win_rate_percent": float|None }
    """
    days = activity.get("days_since_last_game")
    games7 = int(activity.get("games_last_7d", 0))

    winrate = performance.get("win_rate_percent")

    a_color, a_msgs = activity_light(days, games7)
    p_color, p_msgs = performance_light(winrate)
    s_color, s_msgs = stability_light(a_color, p_color)

    # Mensajes: primero estabilidad (institucional), luego actividad y rendimiento
    messages = []
    messages.extend(s_msgs)
    messages.extend(a_msgs)
    messages.extend(p_msgs)

    return {
        "activity": a_color,
        "performance": p_color,
        "stability": s_color,
        "messages": messages,
    }
