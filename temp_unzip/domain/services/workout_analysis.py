from statistics import mean
from typing import Dict, List

from ..models import (
    Workout,
    WorkoutCapacity,
    WorkoutHyroxStation,
    WorkoutLevelTime,
    IntensityLevel,
    EnergyDomain,
    PhysicalCapacity,
)


def _intensity_factor(intensity: IntensityLevel) -> float:
    return {
        IntensityLevel.LOW: 0.8,
        IntensityLevel.MEDIUM: 1.0,
        IntensityLevel.HIGH: 1.25,
    }.get(intensity, 1.0)


def _domain_factor(domain: EnergyDomain) -> float:
    return {
        EnergyDomain.AEROBIC: 0.9,
        EnergyDomain.MIXED: 1.05,
        EnergyDomain.ANAEROBIC: 1.1,
    }.get(domain, 1.0)


def estimate_fatigue_score(workout: Workout) -> float:
    """Quick heuristic for session fatigue."""
    base = workout.estimated_difficulty * _intensity_factor(workout.intensity) * _domain_factor(workout.domain)
    hyrox_weight = _intensity_factor(workout.hyrox_transfer)
    hyrox_component = hyrox_weight * 2
    return round(base + hyrox_component, 2)


def hyrox_transfer_score(stations: List[WorkoutHyroxStation]) -> float:
    if not stations:
        return 0.0
    return round(mean([s.transfer_pct for s in stations]) / 10, 2)


def capacity_focus(capacities: List[WorkoutCapacity]) -> List[Dict[str, str]]:
    top = sorted(capacities, key=lambda c: c.value, reverse=True)[:3]
    return [{"capacity": c.capacity.value, "emphasis": f"{c.value}/100", "note": c.note} for c in top]


def _resolve_level_label(value):
    if not value:
        return "Nivel desconocido"
    return value.value if hasattr(value, "value") else str(value)


def pacing_recommendation(level_times: List[WorkoutLevelTime]) -> Dict[str, str]:
    if not level_times:
        return {"tip": "Mantén controlado el ritmo en los primeros 2-3 minutos.", "range": "Desconocido"}
    fastest = min(level_times, key=lambda t: t.time_minutes)
    slowest = max(level_times, key=lambda t: t.time_minutes)
    fastest_label = _resolve_level_label(fastest.athlete_level)
    return {
        "tip": f"Atleta {fastest_label}: busca {fastest.time_range}. Ajusta descansos para no superar {slowest.time_range}.",
        "range": f"{fastest.time_range} - {slowest.time_range}",
    }


def analyze_workout(workout: Workout) -> Dict[str, object]:
    fatigue = estimate_fatigue_score(workout)
    transfer = hyrox_transfer_score(workout.hyrox_stations)
    capacities = capacity_focus(workout.capacities)
    pacing = pacing_recommendation(workout.level_times)
    return {
        "workout_id": workout.id,
        "fatigue_score": fatigue,
        "hyrox_transfer": transfer,
        "capacity_focus": capacities,
        "pacing": pacing,
        "expected_feel": workout.session_feel,
        "session_load": workout.session_load,
    }
