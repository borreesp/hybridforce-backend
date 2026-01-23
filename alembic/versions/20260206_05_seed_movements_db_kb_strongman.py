"""Seed movements: dumbbell, kettlebell, strongman, and accessories.

Revision ID: 20260206_05_seed_strongman
Revises: 20260206_04_seed_barbell
Create Date: 2026-02-06
"""

import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "20260206_05_seed_strongman"
down_revision = "20260206_04_seed_barbell"
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
        name="Dumbbell Snatch",
        code="dumbbell_snatch",
        category="dumbbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db snatch", "dumbbell snatch", "db sn"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Clean",
        code="dumbbell_clean",
        category="dumbbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db clean", "dumbbell clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Power Clean",
        code="dumbbell_power_clean",
        category="dumbbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db power clean", "dumbbell power clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Clean & Jerk",
        code="dumbbell_clean_and_jerk",
        category="dumbbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db clean and jerk", "db c&j", "dumbbell clean & jerk"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Thruster",
        code="dumbbell_thruster",
        category="dumbbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db thruster", "dumbbell thruster"],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Dumbbell Push Press",
        code="dumbbell_push_press",
        category="dumbbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db push press", "dumbbell push press"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Dumbbell Push Jerk",
        code="dumbbell_push_jerk",
        category="dumbbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db push jerk", "dumbbell push jerk"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Dumbbell Bench Press",
        code="dumbbell_bench_press",
        category="dumbbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db bench press", "dumbbell bench press"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Dumbbell Floor Press",
        code="dumbbell_floor_press",
        category="dumbbell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db floor press", "dumbbell floor press"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Dumbbell Row",
        code="dumbbell_row",
        category="dumbbell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db row", "dumbbell row"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Grip"]},
    ),
    mv(
        name="Dumbbell Deadlift",
        code="dumbbell_deadlift",
        category="dumbbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db deadlift", "dumbbell deadlift"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Romanian Deadlift",
        code="dumbbell_romanian_deadlift",
        category="dumbbell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db rdl", "dumbbell romanian deadlift"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Lunge",
        code="dumbbell_lunge",
        category="dumbbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db lunge", "dumbbell lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Walking Lunge",
        code="dumbbell_walking_lunge",
        category="dumbbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db walking lunge", "dumbbell walking lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Dumbbell Step-Up",
        code="dumbbell_step_up",
        category="dumbbell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["db step up", "dumbbell step-up"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Devil's Press",
        code="devils_press",
        category="dumbbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["devils press", "devil press", "devil's press"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Man Maker",
        code="man_maker",
        category="dumbbell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["man maker", "manmakers"],
        muscles={"primary": ["Pecho", "Posterior"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Dumbbell Farmer Carry",
        code="dumbbell_farmer_carry",
        category="dumbbell",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["db farmer carry", "dumbbell farmer carry", "db carry"],
        muscles={"primary": ["Grip"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Dumbbell Farmer Hold",
        code="dumbbell_farmer_hold",
        category="dumbbell",
        pattern="carry",
        default_metric_unit="time",
        supports_flags=supports(time=True, load=True),
        aliases=["db farmer hold", "dumbbell farmer hold"],
        muscles={"primary": ["Grip"], "secondary": ["Core"]},
    ),
    mv(
        name="Kettlebell Swing",
        code="kettlebell_swing",
        category="kettlebell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=[
            "kb swing",
            "kettlebell swing",
            "kb swings",
            "russian kb swing",
            "american kb swing",
        ],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Grip", "Piernas"]},
    ),
    mv(
        name="Kettlebell Snatch",
        code="kettlebell_snatch",
        category="kettlebell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb snatch", "kettlebell snatch"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Kettlebell Clean",
        code="kettlebell_clean",
        category="kettlebell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb clean", "kettlebell clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Kettlebell Clean & Jerk",
        code="kettlebell_clean_and_jerk",
        category="kettlebell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb clean and jerk", "kb c&j", "kettlebell clean & jerk"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Kettlebell Press",
        code="kettlebell_press",
        category="kettlebell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb press", "kettlebell press"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core"]},
    ),
    mv(
        name="Kettlebell Push Press",
        code="kettlebell_push_press",
        category="kettlebell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb push press", "kettlebell push press"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Kettlebell Push Jerk",
        code="kettlebell_push_jerk",
        category="kettlebell",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb push jerk", "kettlebell push jerk"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Kettlebell Deadlift",
        code="kettlebell_deadlift",
        category="kettlebell",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb deadlift", "kettlebell deadlift"],
        muscles={"primary": ["Posterior"], "secondary": ["Piernas", "Core", "Grip"]},
    ),
    mv(
        name="Kettlebell Sumo Deadlift High Pull",
        code="kettlebell_sdhp",
        category="kettlebell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb sdhp", "kettlebell sdhp", "kb sumo deadlift high pull"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Hombros", "Core", "Grip"]},
    ),
    mv(
        name="Turkish Get-Up",
        code="turkish_get_up",
        category="kettlebell",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["tgu", "turkish get up", "turkish get-up"],
        muscles={"primary": ["Core", "Hombros"], "secondary": ["Piernas"]},
    ),
    mv(
        name="Goblet Squat",
        code="goblet_squat",
        category="kettlebell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["goblet squat", "kb goblet squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Kettlebell Lunge",
        code="kettlebell_lunge",
        category="kettlebell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb lunge", "kettlebell lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Kettlebell Front Rack Lunge",
        code="kettlebell_front_rack_lunge",
        category="kettlebell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb front rack lunge", "kettlebell front rack lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Kettlebell Overhead Lunge",
        code="kettlebell_overhead_lunge",
        category="kettlebell",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb overhead lunge", "kettlebell overhead lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Kettlebell Farmer Carry",
        code="kettlebell_farmer_carry",
        category="kettlebell",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["kb farmer carry", "kettlebell farmer carry"],
        muscles={"primary": ["Grip"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Kettlebell High Pull",
        code="kettlebell_high_pull",
        category="kettlebell",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["kb high pull", "kettlebell high pull"],
        muscles={"primary": ["Hombros", "Posterior"], "secondary": ["Grip", "Core"]},
    ),
    mv(
        name="Wall Ball Shot",
        code="wall_ball_shot",
        category="strongman",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["wall ball", "wallball", "wb", "wbs", "wall ball shot"],
        muscles={"primary": ["Piernas", "Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Med Ball Clean",
        code="med_ball_clean",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["med ball clean", "medicine ball clean", "mb clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Med Ball Slam",
        code="med_ball_slam",
        category="strongman",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["med ball slam", "medicine ball slam", "ball slam"],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Hombros"]},
    ),
    mv(
        name="Box Jump",
        code="box_jump",
        category="strongman",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["box jump", "bj"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Box Jump Over",
        code="box_jump_over",
        category="strongman",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["box jump over", "box jumps over", "bjo"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Step-Up",
        code="step_up",
        category="strongman",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["step up", "step-up"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Broad Jump",
        code="broad_jump",
        category="strongman",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["broad jump", "broad jumps"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Burpee",
        code="burpee",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["burpee", "burpees"],
        muscles={"primary": ["Piernas", "Pecho"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Burpee to Plate",
        code="burpee_to_plate",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["burpee to plate", "burpees to plate", "burpee to plates"],
        muscles={"primary": ["Piernas", "Pecho"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Burpee Over Bar",
        code="burpee_over_bar",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["burpee over bar", "bob"],
        muscles={"primary": ["Piernas", "Pecho"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Burpee Box Jump Over",
        code="burpee_box_jump_over",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["burpee box jump over", "bbjo"],
        muscles={"primary": ["Piernas", "Pecho"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Burpee Broad Jump",
        code="burpee_broad_jump",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["burpee broad jump", "bbj"],
        muscles={"primary": ["Piernas", "Pecho"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Sandbag Clean",
        code="sandbag_clean",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sandbag clean", "sb clean"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Sandbag Carry",
        code="sandbag_carry",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["sandbag carry", "sb carry"],
        muscles={"primary": ["Core", "Grip"], "secondary": ["Piernas", "Posterior"]},
    ),
    mv(
        name="Sandbag Lunge",
        code="sandbag_lunge",
        category="strongman",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sandbag lunge", "sb lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Sandbag Squat",
        code="sandbag_squat",
        category="strongman",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sandbag squat", "sb squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Sandbag Shoulder",
        code="sandbag_shoulder",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["sandbag shoulder", "sb shoulder", "sandbag to shoulder"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Core", "Hombros", "Grip"]},
    ),
    mv(
        name="Farmer Carry",
        code="farmer_carry",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["farmer carry", "farmers carry", "farmer walk"],
        muscles={"primary": ["Grip"], "secondary": ["Core", "Piernas"]},
    ),
    mv(
        name="Farmer Hold",
        code="farmer_hold",
        category="strongman",
        pattern="carry",
        default_metric_unit="time",
        supports_flags=supports(time=True, load=True),
        aliases=["farmer hold", "farmers hold"],
        muscles={"primary": ["Grip"], "secondary": ["Core"]},
    ),
    mv(
        name="Sled Push",
        code="sled_push",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["sled push", "prowler push"],
        muscles={"primary": ["Piernas"], "secondary": ["Core", "Posterior"]},
    ),
    mv(
        name="Sled Pull",
        code="sled_pull",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["sled pull", "prowler pull"],
        muscles={"primary": ["Posterior"], "secondary": ["Grip", "Core", "Piernas"]},
    ),
    mv(
        name="Sled Drag",
        code="sled_drag",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["sled drag", "sled drag back"],
        muscles={"primary": ["Posterior"], "secondary": ["Grip", "Core", "Piernas"]},
    ),
    mv(
        name="Yoke Carry",
        code="yoke_carry",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["yoke carry", "yoke walk"],
        muscles={"primary": ["Core"], "secondary": ["Piernas", "Grip"]},
    ),
    mv(
        name="Tire Flip",
        code="tire_flip",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["tire flip", "tyre flip"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Atlas Stone",
        code="atlas_stone",
        category="strongman",
        pattern="mixed",
        default_metric_unit="reps",
        supports_flags=supports(reps=True, load=True),
        aliases=["atlas stone", "stone to shoulder"],
        muscles={"primary": ["Posterior", "Piernas"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Keg Carry",
        code="keg_carry",
        category="strongman",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True, load=True),
        aliases=["keg carry", "keg walk"],
        muscles={"primary": ["Core"], "secondary": ["Piernas", "Grip"]},
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


