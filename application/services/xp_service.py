from typing import Dict, Optional

XP_MIN = 40
XP_MAX = 600
LEVEL_FACTOR_MAX = 1.15
LEVEL_FACTOR_MIN = 0.65
FATIGUE_EXPONENT = 1.3


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _level_to_factor(level: Optional[int]) -> float:
    if level is None:
        return 1.0
    return _clamp(LEVEL_FACTOR_MAX - 0.01 * level, LEVEL_FACTOR_MIN, LEVEL_FACTOR_MAX)


def compute_xp_estimate(fatigue_0_10: float, athlete_level: Optional[int]) -> Dict[str, float]:
    """
    Estimate XP using fatigue (0-10) and a level factor so higher levels progres slightly slower.
    Returns components for transparency.
    """
    norm = _clamp(fatigue_0_10 / 10.0, 0.0, 1.0)
    xp_base = XP_MIN + (XP_MAX - XP_MIN) * (norm ** FATIGUE_EXPONENT)
    level_factor = _level_to_factor(athlete_level)
    xp = round(xp_base * level_factor)
    return {
        "xp": xp,
        "xp_base": xp_base,
        "fatigue_norm": norm,
        "level_factor": level_factor,
    }
