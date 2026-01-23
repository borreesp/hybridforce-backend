"""Seed movements: ERGs + monostructural.

Revision ID: 20260206_02_seed_ergs
Revises: 20260206_01_mov_catalog
Create Date: 2026-02-06
"""

import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "20260206_02_seed_ergs"
down_revision = "20260206_01_mov_catalog"
branch_labels = None
depends_on = None


def normalize_alias(value: str) -> str:
    if not value:
        return ""
    text_value = value.lower().strip()
    text_value = text_value.replace("\\u2013", "-").replace("\\u2014", "-")
    for ch in ".,;:()[]{}'\"":
        text_value = text_value.replace(ch, " ")
    while "--" in text_value:
        text_value = text_value.replace("--", "-")
    text_value = re.sub(r"[^a-z0-9\-\s]", " ", text_value)
    text_value = re.sub(r"\s+", " ", text_value).strip()
    return text_value


def slugify_code(value: str) -> str:
    base = normalize_alias(value)
    base = base.replace("-", " ")
    return base.replace(" ", "_")


def supports(reps=False, load=False, distance=False, time=False, calories=False):
    return {
        "reps": reps,
        "load": load,
        "distance": distance,
        "time": time,
        "calories": calories,
    }


def mv(
    name,
    code=None,
    category=None,
    pattern=None,
    default_metric_unit=None,
    supports_flags=None,
    aliases=None,
    muscles=None,
    skill_level=None,
    default_load_unit=None,
):
    return {
        "name": name,
        "code": code,
        "category": category,
        "pattern": pattern,
        "default_metric_unit": default_metric_unit,
        "supports": supports_flags or supports(),
        "aliases": aliases or [],
        "muscles": muscles or {},
        "skill_level": skill_level,
        "default_load_unit": default_load_unit,
    }


def expand_aliases(aliases):
    expanded = []
    for alias in aliases or []:
        base = (alias or "").strip()
        if not base:
            continue
        expanded.append(base)
        lower = base.lower()
        if "-" in lower:
            expanded.append(lower.replace("-", " "))
            expanded.append(lower.replace("-", ""))
        if " " in lower:
            expanded.append(lower.replace(" ", "-"))
            expanded.append(lower.replace(" ", ""))
        if "/" in lower:
            expanded.append(lower.replace("/", " "))
            expanded.append(lower.replace("/", "-"))
        if not lower.endswith("s"):
            expanded.append(lower + "s")
        if lower.endswith("s"):
            expanded.append(lower[:-1])
    deduped = []
    seen = set()
    for alias in expanded:
        norm = normalize_alias(alias)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        deduped.append(alias)
    return deduped


def get_or_create_movement(name, **fields):
    conn = op.get_bind()
    row = conn.execute(
        text(
            "SELECT id, code, category, description, pattern, default_load_unit, default_metric_unit, "
            "supports_reps, supports_load, supports_distance, supports_time, supports_calories, skill_level "
            "FROM movements WHERE lower(name)=lower(:name)"
        ),
        {"name": name},
    ).mappings().fetchone()

    if row:
        updates = {}
        for key in [
            "code",
            "category",
            "description",
            "pattern",
            "default_load_unit",
            "default_metric_unit",
            "skill_level",
        ]:
            if fields.get(key) is not None and (row.get(key) is None or str(row.get(key)).strip() == ""):
                updates[key] = fields.get(key)
        for key in [
            "supports_reps",
            "supports_load",
            "supports_distance",
            "supports_time",
            "supports_calories",
        ]:
            if fields.get(key) is True and (row.get(key) is None or row.get(key) is False):
                updates[key] = True
        if updates:
            conn.execute(
                text(
                    "UPDATE movements SET " + ", ".join(f"{k}=:{k}" for k in updates.keys()) + " WHERE lower(name)=lower(:name)"
                ),
                {**updates, "name": name},
            )
        return row["id"]

    insert_fields = {"name": name}
    insert_fields.update(fields)
    columns = ", ".join(insert_fields.keys())
    values = ", ".join(f":{k}" for k in insert_fields.keys())
    conn.execute(text(f"INSERT INTO movements ({columns}) VALUES ({values})"), insert_fields)
    created = conn.execute(
        text("SELECT id FROM movements WHERE lower(name)=lower(:name)"),
        {"name": name},
    ).mappings().fetchone()
    return created["id"] if created else None


def upsert_alias(movement_id, alias, source="import"):
    if not alias:
        return
    alias_value = alias.strip()
    if not alias_value:
        return
    normalized = normalize_alias(alias_value)
    if not normalized:
        return
    conn = op.get_bind()
    exists = conn.execute(
        text(
            "SELECT 1 FROM movement_aliases WHERE movement_id=:movement_id AND alias_normalized=:alias_normalized"
        ),
        {"movement_id": movement_id, "alias_normalized": normalized},
    ).fetchone()
    if exists:
        return
    conn.execute(
        text(
            "INSERT INTO movement_aliases (movement_id, alias, alias_normalized, source) "
            "VALUES (:movement_id, :alias, :alias_normalized, :source)"
        ),
        {
            "movement_id": movement_id,
            "alias": alias_value,
            "alias_normalized": normalized,
            "source": source,
        },
    )


def link_muscles(movement_id, primary_codes=None, secondary_codes=None):
    conn = op.get_bind()
    for code in (primary_codes or []):
        row = conn.execute(text("SELECT id FROM muscle_groups WHERE code=:code"), {"code": code}).fetchone()
        if not row:
            continue
        exists = conn.execute(
            text(
                "SELECT 1 FROM movement_muscles WHERE movement_id=:movement_id AND muscle_group_id=:muscle_group_id"
            ),
            {"movement_id": movement_id, "muscle_group_id": row[0]},
        ).fetchone()
        if not exists:
            conn.execute(
                text(
                    "INSERT INTO movement_muscles (movement_id, muscle_group_id, is_primary) "
                    "VALUES (:movement_id, :muscle_group_id, :is_primary)"
                ),
                {"movement_id": movement_id, "muscle_group_id": row[0], "is_primary": True},
            )
    for code in (secondary_codes or []):
        row = conn.execute(text("SELECT id FROM muscle_groups WHERE code=:code"), {"code": code}).fetchone()
        if not row:
            continue
        exists = conn.execute(
            text(
                "SELECT 1 FROM movement_muscles WHERE movement_id=:movement_id AND muscle_group_id=:muscle_group_id"
            ),
            {"movement_id": movement_id, "muscle_group_id": row[0]},
        ).fetchone()
        if not exists:
            conn.execute(
                text(
                    "INSERT INTO movement_muscles (movement_id, muscle_group_id, is_primary) "
                    "VALUES (:movement_id, :muscle_group_id, :is_primary)"
                ),
                {"movement_id": movement_id, "muscle_group_id": row[0], "is_primary": False},
            )


MOVEMENTS = [
    mv(
        name="Row",
        code="row",
        category="monostructural",
        pattern="mixed",
        default_metric_unit="calories",
        supports_flags=supports(distance=True, time=True, calories=True),
        aliases=[
            "row",
            "rower",
            "rowing",
            "concept2 row",
            "c2 row",
            "erg row",
            "row erg",
            "row machine",
            "cal row",
            "cals row",
            "row calories",
            "row cal",
            "20 cals",
            "20 cal row",
            "20 cals row",
            "row 20 cals",
            "row 20 cal",
            "remo",
        ],
        muscles={"primary": ["Piernas", "Posterior"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="SkiErg",
        code="skierg",
        category="monostructural",
        pattern="mixed",
        default_metric_unit="calories",
        supports_flags=supports(distance=True, time=True, calories=True),
        aliases=[
            "ski",
            "skierg",
            "ski erg",
            "concept2 ski",
            "c2 ski",
            "ski machine",
            "cal ski",
            "cals ski",
            "ski calories",
            "skierg cals",
            "ski erg cals",
            "esqui",
        ],
        muscles={"primary": ["Hombros", "Posterior"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="BikeErg",
        code="bike_erg",
        category="monostructural",
        pattern="mixed",
        default_metric_unit="calories",
        supports_flags=supports(distance=True, time=True, calories=True),
        aliases=[
            "bikeerg",
            "bike erg",
            "concept2 bike",
            "c2 bike",
            "erg bike",
            "bike erg cals",
            "bike erg calories",
            "assault bike erg",
            "c2 bike erg",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="AirBike",
        code="assault_bike",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="calories",
        supports_flags=supports(time=True, calories=True),
        aliases=[
            "airbike",
            "air bike",
            "assault",
            "assault bike",
            "ab",
            "bike assault",
            "fan bike",
            "airbike cals",
            "air bike calories",
        ],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core"]},
    ),
    mv(
        name="Echo Bike",
        code="echo_bike",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="calories",
        supports_flags=supports(time=True, calories=True),
        aliases=[
            "echo",
            "echo bike",
            "rogue echo",
            "rogue bike",
            "echo air bike",
            "echo cals",
        ],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core"]},
    ),
    mv(
        name="Assault Runner",
        code="assault_runner",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=[
            "assault runner",
            "air runner",
            "treadmill",
            "treadmill run",
            "run mill",
            "assault run",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Run",
        code="run",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=[
            "run",
            "running",
            "jog",
            "jogging",
            "run 200m",
            "run 400m",
            "run 800m",
            "run 1k",
            "run 5k",
            "run 10k",
            "run meters",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Sprint",
        code="sprint",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=[
            "sprint",
            "sprints",
            "dash",
            "100m sprint",
            "200m sprint",
            "short sprint",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Shuttle Run",
        code="shuttle_run",
        category="monostructural",
        pattern="cardio",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=[
            "shuttle run",
            "shuttle",
            "shuttles",
            "suicides",
            "beep test",
            "5-10-5",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Single Under",
        code="single_under",
        category="monostructural",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=[
            "single under",
            "single unders",
            "jump rope",
            "jump rope su",
            "su",
            "singles",
            "rope skips",
            "skips",
            "jumping rope",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Double Under",
        code="double_under",
        category="monostructural",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=[
            "double under",
            "double unders",
            "du",
            "dubs",
            "double under jump rope",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Triple Under",
        code="triple_under",
        category="monostructural",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=[
            "triple under",
            "triple unders",
            "tu",
        ],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
]


def upgrade():
    for item in MOVEMENTS:
        support_flags = item.get("supports", {})
        fields = {
            "code": item.get("code") or slugify_code(item["name"]),
            "category": item.get("category"),
            "description": item.get("description"),
            "pattern": item.get("pattern"),
            "default_load_unit": item.get("default_load_unit"),
            "default_metric_unit": item.get("default_metric_unit"),
            "supports_reps": bool(support_flags.get("reps")),
            "supports_load": bool(support_flags.get("load")),
            "supports_distance": bool(support_flags.get("distance")),
            "supports_time": bool(support_flags.get("time")),
            "supports_calories": bool(support_flags.get("calories")),
            "skill_level": item.get("skill_level"),
        }
        movement_id = get_or_create_movement(item["name"], **fields)
        alias_list = [item["name"]] + (item.get("aliases") or [])
        for alias in expand_aliases(alias_list):
            upsert_alias(movement_id, alias, source="import")
        muscles = item.get("muscles") or {}
        link_muscles(
            movement_id,
            primary_codes=muscles.get("primary", []),
            secondary_codes=muscles.get("secondary", []),
        )


def downgrade():
    # Seed only; do not delete to avoid breaking existing data
    pass


