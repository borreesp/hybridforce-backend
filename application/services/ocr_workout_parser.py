from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import List, Optional

from infrastructure.db.models import MovementORM


@dataclass
class ParsedMetric:
    type: str  # "reps" | "cals" | "distance_meters" | "duration_seconds"
    value: Optional[float] = None


@dataclass
class ParsedItem:
    raw: str
    movement_id: Optional[int] = None
    unresolved_label: Optional[str] = None
    reps: Optional[float] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[float] = None
    calories: Optional[float] = None
    load: Optional[float] = None
    load_unit: Optional[str] = None
    is_max: bool = False
    metric: Optional[ParsedMetric] = None


@dataclass
class ParsedScenario:
    label: str
    items: List[ParsedItem]


@dataclass
class ParsedBlock:
    block_type: str
    rounds: Optional[int] = None
    work_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    scenarios: List[ParsedScenario] = None


@dataclass
class WorkoutDraft:
    source_text: str
    title: Optional[str]
    detected_style: str
    rounds: Optional[int]
    work_seconds: Optional[int]
    rest_seconds: Optional[int]
    time_cap_seconds: Optional[int]
    blocks: List[ParsedBlock]
    unresolved: List[dict]

    def to_dict(self):
        return {
            "source_text": self.source_text,
            "title": self.title,
            "detected": {
                "workout_style": self.detected_style,
                "rounds": self.rounds,
                "work_seconds": self.work_seconds,
                "rest_seconds": self.rest_seconds,
                "time_cap_seconds": self.time_cap_seconds,
            },
            "blocks": [
                {
                    "block_type": b.block_type,
                    "rounds": b.rounds,
                    "work_seconds": b.work_seconds,
                    "rest_seconds": b.rest_seconds,
                    "scenarios": [
                        {
                            "label": s.label,
                            "items": [asdict(i) for i in s.items],
                        }
                        for s in (b.scenarios or [])
                    ],
                }
                for b in self.blocks
            ],
            "unresolved": self.unresolved,
        }


ALIAS = {
    "kb swing": "Kettlebell Swing",
    "kb swings": "Kettlebell Swing",
    "kettlebell swing": "Kettlebell Swing",
    "burpees to plate": "Burpee to Plate",
    "burpee to plate": "Burpee to Plate",
    "broad jump": "Broad Jump",
    "broad jumps": "Broad Jump",
    "jumping lunge": "Jumping Lunge",
    "jumping lunges": "Jumping Lunge",
    "run": "Run",
    "row": "Row",
    "bike": "AirBike",
    "ski": "SkiErg",
    "t2b": "Toes-to-Bar",
    "toes to bar": "Toes-to-Bar",
    "20 cals": "Row",
}


def _norm(text: str) -> str:
    if not text:
        return ""
    cleaned = text.lower().strip()
    cleaned = cleaned.replace("\u2013", "-").replace("\u2014", "-")
    cleaned = re.sub(r"[\\.,;:\\(\\)\\[\\]\\{\\}'\\\"]", " ", cleaned)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = re.sub(r"[^a-z0-9\\-\\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _build_alias_index(movements: list[MovementORM]) -> tuple[dict[str, int], list[str], dict[str, int]]:
    alias_map: dict[str, int] = {}
    name_map: dict[str, int] = {}
    for m in movements:
        name_norm = _norm(getattr(m, "name", "") or "")
        if name_norm:
            name_map[name_norm] = m.id
            alias_map.setdefault(name_norm, m.id)
        aliases = getattr(m, "aliases", None) or []
        for alias in aliases:
            alias_text = getattr(alias, "alias", None) or ""
            alias_norm = getattr(alias, "alias_normalized", None) or _norm(alias_text)
            if alias_norm and alias_norm not in alias_map:
                alias_map[alias_norm] = m.id

    for raw_alias, target_name in ALIAS.items():
        target_norm = _norm(target_name)
        target_id = name_map.get(target_norm)
        if not target_id:
            continue
        alias_norm = _norm(raw_alias)
        if alias_norm and alias_norm not in alias_map:
            alias_map[alias_norm] = target_id

    alias_keys = sorted(alias_map.keys(), key=len, reverse=True)
    return alias_map, alias_keys, name_map


def parse_duration_to_seconds(raw: str) -> Optional[int]:
    if not raw:
        return None
    raw = raw.replace("’", "'").replace("´", "'")
    m = re.match(r"(\d+)\s*(?:min|m)\b", raw, re.IGNORECASE)
    if m:
        return int(m.group(1)) * 60
    m = re.match(r"(\d+)\s*(?:sec|s)\b", raw, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.match(r"(\d+)\s*['’]", raw)
    if m:
        return int(m.group(1)) * 60
    return None


def detect_style(text: str) -> str:
    up = text.upper()
    if "EMOM" in up:
        return "emom"
    if "AMRAP" in up:
        return "amrap"
    if "FOR TIME" in up or "FT" in up:
        return "for_time"
    if " ON " in f" {up} " and " OFF" in up:
        return "intervals"
    if "INTERVAL" in up:
        return "intervals"
    return "unknown"


def parse_rounds(text: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*(rondas?|rounds?)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_work_rest(text: str) -> tuple[Optional[int], Optional[int]]:
    m = re.search(r"(\d+)\s*[’'´]?\s*on", text, re.IGNORECASE)
    work = parse_duration_to_seconds(m.group(1) + "'") if m else None
    m2 = re.search(r"(\d+)\s*[’'´]?\s*off", text, re.IGNORECASE)
    rest = parse_duration_to_seconds(m2.group(1) + "'") if m2 else None
    return work, rest


def split_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def parse_scenarios(lines: list[str]) -> list[ParsedScenario]:
    scenarios: list[ParsedScenario] = []
    current: Optional[ParsedScenario] = None
    for ln in lines:
        scen_match = re.match(r"^([A-C])[)\.:]\s*(.+)$", ln, re.IGNORECASE)
        if scen_match:
            label = scen_match.group(1).upper()
            content = scen_match.group(2).strip()
            current = ParsedScenario(label=label, items=parse_items(content))
            scenarios.append(current)
        elif current:
            # continuation line, append as separate item
            current.items.extend(parse_items(ln))
    return scenarios


def parse_items(content: str) -> list[ParsedItem]:
    parts = [p.strip() for p in re.split(r"\s*\+\s*", content) if p.strip()]
    items: list[ParsedItem] = []
    for part in parts:
        is_max = bool(re.search(r"\bmax|\bmáx", part, re.IGNORECASE))
        reps = None
        distance = None
        cals = None
        duration = None
        load = None
        load_unit = None

        if m := re.search(r"(\d+)\s*cals?", part, re.IGNORECASE):
            cals = float(m.group(1))
        elif m := re.search(r"(\d+)\s*m\b", part, re.IGNORECASE):
            distance = float(m.group(1))
        elif m := re.search(r"(\d+)\s*(kg|lb|lbs)", part, re.IGNORECASE):
            load = float(m.group(1))
            load_unit = m.group(2)
        elif m := re.search(r"(\d+)\b", part):
            reps = float(m.group(1))

        metric: Optional[ParsedMetric] = None
        if cals is not None:
            metric = ParsedMetric(type="cals", value=cals)
        elif distance is not None:
            metric = ParsedMetric(type="distance_meters", value=distance)
        elif reps is not None:
            metric = ParsedMetric(type="reps", value=reps)
        elif is_max:
            metric = ParsedMetric(type="reps", value=None)

        items.append(
            ParsedItem(
                raw=part,
                reps=reps,
                distance_meters=distance,
                calories=cals,
                duration_seconds=duration,
                load=load,
                load_unit=load_unit,
                is_max=is_max,
                metric=metric,
            )
        )
    return items


def match_movement(
    raw: str,
    movements: list[MovementORM],
    alias_map: dict[str, int],
    alias_keys: list[str],
) -> tuple[Optional[int], list[dict]]:
    norm = _norm(raw)
    if norm in alias_map:
        return alias_map[norm], []
    for key in alias_keys:
        if not key or len(key) < 4:
            continue
        if key in norm:
            return alias_map[key], []

    tokens = [t for t in re.split(r"[\s/]", norm) if t]
    suggestions = []
    for m in movements:
        lower = m.name.lower()
        score = sum(1 for t in tokens if t and t in lower)
        if score:
            suggestions.append({"movement_id": m.id, "name": m.name, "score": score})
    suggestions = sorted(suggestions, key=lambda s: s["score"], reverse=True)[:3]
    return None, [{"movement_id": s["movement_id"], "name": s["name"]} for s in suggestions]


def parse_workout_text(text: str, movements: list[MovementORM]) -> WorkoutDraft:
    lines = split_lines(text)
    title = lines[0] if lines else None
    rounds = None
    work_seconds = None
    rest_seconds = None
    detected_style = detect_style(text)

    for ln in lines:
        if not rounds:
            rounds = parse_rounds(ln)
        if detected_style == "intervals":
            w, r = parse_work_rest(ln)
            work_seconds = work_seconds or w
            rest_seconds = rest_seconds or r

    scenarios = parse_scenarios(lines)
    unresolved: list[dict] = []

    alias_map, alias_keys, _ = _build_alias_index(movements)
    allowed_cal_ids = {
        m.id
        for m in movements
        if getattr(m, "supports_calories", False)
        or (getattr(m, "code", "") or "").lower() in {"row", "skierg", "bike_erg", "assault_bike", "echo_bike"}
        or (getattr(m, "name", "").lower() in {"row", "skierg", "assault bike", "echo bike", "airbike", "air bike", "bikeerg", "bike erg"})
    }

    for scen in scenarios:
        for item in scen.items:
            mv_id, suggestions = match_movement(item.raw, movements, alias_map, alias_keys)
            if mv_id:
                item.movement_id = mv_id
            else:
                item.unresolved_label = item.raw
                if suggestions:
                    unresolved.append({"raw": item.raw, "suggestions": suggestions})
                else:
                    unresolved.append({"raw": item.raw, "suggestions": []})

    block = ParsedBlock(
        block_type=detected_style if detected_style != "unknown" else "intervals",
        rounds=rounds,
        work_seconds=work_seconds,
        rest_seconds=rest_seconds,
        scenarios=scenarios,
    )
    # Seguridad: no permitimos calorías en movimientos que no sean ERG
    for scen in block.scenarios or []:
        for it in scen.items:
            if it.calories is not None and it.movement_id and it.movement_id not in allowed_cal_ids:
                it.calories = None

    return WorkoutDraft(
        source_text=text,
        title=title,
        detected_style=detected_style,
        rounds=rounds,
        work_seconds=work_seconds,
        rest_seconds=rest_seconds,
        time_cap_seconds=None,
        blocks=[block],
        unresolved=unresolved,
    )
