"""Seed movements: barbell and weightlifting.

Revision ID: 20260206_04_seed_barbell
Revises: 20260206_03_seed_gym
Create Date: 2026-02-06
"""

import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "20260206_04_seed_barbell"
down_revision = "20260206_03_seed_gym"
branch_labels = None
depends_on = None


def normalize_alias(value: str) -> str:
    if not value:
        return ""
    text_value = value.lower().strip()
    text_value = text_value.replace("\u2013", "-").replace("\u2014", "-")
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
        name="Deadlift",
        code="deadlift",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["deadlift", "dead lift", "dl"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Romanian Deadlift",
        code="romanian_deadlift",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["romanian deadlift", "rdl"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Stiff-Leg Deadlift",
        code="stiff_leg_deadlift",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["stiff leg deadlift", "stiff-leg deadlift"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Sumo Deadlift",
        code="sumo_deadlift",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sumo deadlift", "sumo dl"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Sumo Deadlift High Pull",
        code="sumo_deadlift_high_pull",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sumo deadlift high pull", "sdhp"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Grip", "Core"]},
    ),
    mv(
        name="Good Morning",
        code="good_morning",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["good morning", "gm"],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Back Squat",
        code="back_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["back squat", "bs"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Front Squat",
        code="front_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["front squat", "fs"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Overhead Squat",
        code="overhead_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["overhead squat", "ohs"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Box Squat",
        code="box_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["box squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Pause Squat",
        code="pause_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["pause squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Zercher Squat",
        code="zercher_squat",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["zercher squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Zercher Lunge",
        code="zercher_lunge",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["zercher lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Thruster",
        code="thruster",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["thruster", "thrusters"],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Strict Press",
        code="strict_press",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["strict press", "shoulder press", "military press", "sp"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core"]},
    ),
    mv(
        name="Push Press",
        code="push_press",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["push press", "pp"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Piernas", "Core"]},
    ),
    mv(
        name="Push Jerk",
        code="push_jerk",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["push jerk", "pj"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Piernas", "Core"]},
    ),
    mv(
        name="Split Jerk",
        code="split_jerk",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["split jerk"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Piernas", "Core"]},
    ),
    mv(
        name="Power Jerk",
        code="power_jerk",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["power jerk"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Piernas", "Core"]},
    ),
    mv(
        name="Jerk",
        code="jerk",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["jerk", "shoulder jerk"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Piernas", "Core"]},
    ),
    mv(
        name="Clean",
        code="clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Power Clean",
        code="power_clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["power clean", "pc"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Squat Clean",
        code="squat_clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["squat clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Hang Power Clean",
        code="hang_power_clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang power clean", "hpc"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Hang Squat Clean",
        code="hang_squat_clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang squat clean", "hsc"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Muscle Clean",
        code="muscle_clean",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["muscle clean"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Clean Pull",
        code="clean_pull",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["clean pull"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Grip", "Core"]},
    ),
    mv(
        name="Hang Clean",
        code="hang_clean",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Snatch",
        code="snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["snatch"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Power Snatch",
        code="power_snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["power snatch", "ps"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Squat Snatch",
        code="squat_snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["squat snatch"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Hang Power Snatch",
        code="hang_power_snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang power snatch", "hps"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Hang Squat Snatch",
        code="hang_squat_snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang squat snatch", "hss"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Muscle Snatch",
        code="muscle_snatch",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["muscle snatch"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Snatch Pull",
        code="snatch_pull",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["snatch pull"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Grip", "Core"]},
    ),
    mv(
        name="Snatch Balance",
        code="snatch_balance",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["snatch balance"],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core"]},
    ),
    mv(
        name="Snatch Grip Deadlift",
        code="snatch_grip_deadlift",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["snatch grip deadlift", "sgdl"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Clean & Jerk",
        code="clean_and_jerk",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["clean and jerk", "c&j", "cj", "clean & jerk"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Cluster",
        code="cluster",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["cluster", "squat clean thruster"],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Front Rack Lunge",
        code="front_rack_lunge",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["front rack lunge", "fr lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Overhead Lunge",
        code="overhead_lunge",
        category="barbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["overhead lunge", "oh lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Bench Press",
        code="bench_press",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["bench press", "bp"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Incline Bench Press",
        code="incline_bench_press",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["incline bench press", "incline bench"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Floor Press",
        code="floor_press",
        category="barbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["floor press"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Barbell Row",
        code="barbell_row",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["barbell row", "bent over row", "bb row"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Grip"]},
    ),
    mv(
        name="Upright Row",
        code="upright_row",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["upright row", "high pull"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Grip"]},
    ),
    mv(
        name="Barbell Curl",
        code="barbell_curl",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["barbell curl", "bb curl"],
        muscles={"primary": ["Brazos"], "secondary": ["Grip"]},
    ),
    mv(
        name="Barbell Shrug",
        code="barbell_shrug",
        category="barbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["barbell shrug", "shrug"],
        muscles={"primary": ["Hombros"], "secondary": ["Grip"]},
    ),
    mv(
        name="Hip Thrust",
        code="hip_thrust",
        category="barbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hip thrust", "barbell hip thrust"],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Overhead Carry",
        code="overhead_carry",
        category="barbell",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["overhead carry", "barbell overhead carry", "oh carry"],
        muscles={"primary": ["Hombros"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Hang Snatch",
        code="hang_snatch",
        category="barbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["hang snatch"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
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


