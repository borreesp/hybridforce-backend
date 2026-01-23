"""Seed movements: gymnastics catalog.

Revision ID: 20260206_03_seed_gym
Revises: 20260206_02_seed_ergs
Create Date: 2026-02-06
"""

import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "20260206_03_seed_gym"
down_revision = "20260206_02_seed_ergs"
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
        name="Pull-Up",
        code="pull_up",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=[
            "pull up",
            "pull-up",
            "pullup",
            "strict pull-up",
            "kipping pull-up",
            "butterfly pull-up",
        ],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Chest-to-Bar",
        code="chest_to_bar",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=[
            "chest to bar",
            "c2b",
            "ctb",
            "chest-to-bar pull-up",
        ],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Chin-Up",
        code="chin_up",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["chin up", "chin-up", "chinup"],
        muscles={"primary": ["Brazos", "Posterior"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Ring Row",
        code="ring_row",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ring row", "ring rows", "australian pull-up", "body row"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core"]},
    ),
    mv(
        name="Toes-to-Bar",
        code="toes_to_bar",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["toes to bar", "t2b", "ttb", "toes2bar"],
        muscles={"primary": ["Core"], "secondary": ["Grip", "Posterior"]},
    ),
    mv(
        name="Knees-to-Elbows",
        code="knees_to_elbows",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["knees to elbows", "k2e", "knees-to-elbows"],
        muscles={"primary": ["Core"], "secondary": ["Grip", "Posterior"]},
    ),
    mv(
        name="Hanging Knee Raise",
        code="hanging_knee_raise",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["hanging knee raise", "hanging knees", "knee raise"],
        muscles={"primary": ["Core"], "secondary": ["Grip"]},
    ),
    mv(
        name="Hanging Leg Raise",
        code="hanging_leg_raise",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["hanging leg raise", "leg raise", "hanging legs"],
        muscles={"primary": ["Core"], "secondary": ["Grip"]},
    ),
    mv(
        name="Bar Muscle-Up",
        code="bar_muscle_up",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["bar muscle-up", "bar muscle up", "bmu"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
        skill_level="advanced",
    ),
    mv(
        name="Ring Muscle-Up",
        code="ring_muscle_up",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ring muscle-up", "ring muscle up", "rmu"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
        skill_level="advanced",
    ),
    mv(
        name="Ring Dip",
        code="ring_dip",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ring dip", "ring dips"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Bar Dip",
        code="bar_dip",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["bar dip", "straight bar dip"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Rope Climb",
        code="rope_climb",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["rope climb", "legless rope climb", "rope climb legless"],
        muscles={"primary": ["Brazos", "Posterior"], "secondary": ["Grip", "Core"]},
    ),
    mv(
        name="Rope Pull",
        code="rope_pull",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["rope pull", "rope pulls"],
        muscles={"primary": ["Brazos", "Posterior"], "secondary": ["Grip", "Core"]},
    ),
    mv(
        name="Dead Hang",
        code="dead_hang",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["dead hang", "hang", "bar hang"],
        muscles={"primary": ["Grip"], "secondary": ["Posterior", "Brazos"]},
    ),
    mv(
        name="Flexed Arm Hang",
        code="flexed_arm_hang",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["flexed arm hang", "active hang", "chin over bar hold"],
        muscles={"primary": ["Brazos", "Grip"], "secondary": ["Posterior"]},
    ),
    mv(
        name="L-Hang",
        code="l_hang",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["l hang", "l-hang"],
        muscles={"primary": ["Core"], "secondary": ["Grip"]},
    ),
    mv(
        name="L-Sit",
        code="l_sit",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["l sit", "l-sit", "lsit"],
        muscles={"primary": ["Core"], "secondary": ["Hombros"]},
    ),
    mv(
        name="V-Up",
        code="v_up",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["v up", "v-up", "vups"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Sit-Up",
        code="sit_up",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["sit up", "sit-up", "abmat sit-up"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="GHD Sit-up",
        code="ghd_situp",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ghd situp", "ghd sit-up", "ghd sit up"],
        muscles={"primary": ["Core"], "secondary": ["Posterior"]},
    ),
    mv(
        name="Hollow Hold",
        code="hollow_hold",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["hollow hold", "hollow body hold"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Hollow Rock",
        code="hollow_rock",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["hollow rock", "hollow rocks", "hollow rockers"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Arch Hold",
        code="arch_hold",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["arch hold", "superman hold"],
        muscles={"primary": ["Posterior"]},
    ),
    mv(
        name="Arch Rock",
        code="arch_rock",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["arch rock", "superman rock"],
        muscles={"primary": ["Posterior"]},
    ),
    mv(
        name="Plank",
        code="plank",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["plank", "front plank"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Side Plank",
        code="side_plank",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["side plank", "side plank hold"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Plank Walk",
        code="plank_walk",
        category="gymnastics",
        pattern="core",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["plank walk", "plank walks"],
        muscles={"primary": ["Core"], "secondary": ["Hombros"]},
    ),
    mv(
        name="Handstand Push-up",
        code="handstand_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["hspu", "handstand push up", "strict hspu", "kipping hspu"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core"]},
        skill_level="advanced",
    ),
    mv(
        name="Handstand Walk",
        code="handstand_walk",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["handstand walk", "hsw", "handstand walking"],
        muscles={"primary": ["Hombros", "Core"], "secondary": ["Brazos"]},
        skill_level="advanced",
    ),
    mv(
        name="Handstand Hold",
        code="handstand_hold",
        category="gymnastics",
        pattern="push",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["handstand hold", "handstand hold wall"],
        muscles={"primary": ["Hombros", "Core"]},
    ),
    mv(
        name="Wall Walk",
        code="wall_walk",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["wall walk", "wall walks"],
        muscles={"primary": ["Hombros", "Core"], "secondary": ["Brazos"]},
    ),
    mv(
        name="Pike Push-Up",
        code="pike_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["pike push up", "pike push-up", "pike press"],
        muscles={"primary": ["Hombros", "Brazos"], "secondary": ["Core"]},
    ),
    mv(
        name="Push-Up",
        code="push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["push up", "push-up", "press up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Hand-Release Push-Up",
        code="hand_release_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["hand release push up", "hrpu", "hand-release push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Ring Push-Up",
        code="ring_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ring push up", "ring push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Deficit Push-Up",
        code="deficit_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["deficit push up", "deficit push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Clapping Push-Up",
        code="clapping_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["clapping push up", "clap push-up", "plyo push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Diamond Push-Up",
        code="diamond_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["diamond push up", "close grip push-up"],
        muscles={"primary": ["Brazos", "Pecho"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Archer Push-Up",
        code="archer_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["archer push up", "archer push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Spiderman Push-Up",
        code="spiderman_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["spiderman push up", "spiderman push-up"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Shoulder Tap Push-Up",
        code="shoulder_tap_push_up",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["shoulder tap push up", "push up shoulder tap"],
        muscles={"primary": ["Pecho", "Brazos"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Air Squat",
        code="air_squat",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["air squat", "bodyweight squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Pistol Squat",
        code="pistol_squat",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["pistol squat", "single leg squat", "pistols"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Jump Squat",
        code="jump_squat",
        category="gymnastics",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["jump squat", "jumping squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Jumping Lunge",
        code="jumping_lunge",
        category="gymnastics",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["jumping lunge", "jump lunge", "jumping lunges"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Walking Lunge",
        code="walking_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["walking lunge", "walking lunges"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Alternating Lunge",
        code="alternating_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["alternating lunge", "alt lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Reverse Lunge",
        code="reverse_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["reverse lunge", "back lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Forward Lunge",
        code="forward_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["forward lunge", "front lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Lateral Lunge",
        code="lateral_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["lateral lunge", "side lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Split Squat",
        code="split_squat",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["split squat", "static lunge"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Cossack Squat",
        code="cossack_squat",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["cossack squat", "side squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Bear Crawl",
        code="bear_crawl",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["bear crawl", "bear crawls"],
        muscles={"primary": ["Core"], "secondary": ["Hombros", "Piernas"]},
    ),
    mv(
        name="Crab Walk",
        code="crab_walk",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["crab walk", "crab walks"],
        muscles={"primary": ["Core"], "secondary": ["Hombros", "Piernas"]},
    ),
    mv(
        name="Inchworm",
        code="inchworm",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["inchworm", "inch worm"],
        muscles={"primary": ["Core"], "secondary": ["Hombros", "Piernas"]},
    ),
    mv(
        name="Spiderman Crawl",
        code="spiderman_crawl",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["spiderman crawl", "spiderman crawl"],
        muscles={"primary": ["Core"], "secondary": ["Hombros", "Piernas"]},
    ),
    mv(
        name="Mountain Climber",
        code="mountain_climber",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["mountain climber", "mountain climbers"],
        muscles={"primary": ["Core"], "secondary": ["Hombros", "Piernas"]},
    ),
    mv(
        name="Duck Walk",
        code="duck_walk",
        category="gymnastics",
        pattern="carry",
        default_metric_unit="distance_meters",
        supports_flags=supports(distance=True, time=True),
        aliases=["duck walk", "duck walks"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Russian Twist",
        code="russian_twist",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["russian twist", "russian twists"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Flutter Kick",
        code="flutter_kick",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["flutter kick", "flutter kicks"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Scissor Kick",
        code="scissor_kick",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["scissor kick", "scissor kicks"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Bicycle Crunch",
        code="bicycle_crunch",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["bicycle crunch", "bicycle crunches"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="GHD Hip Extension",
        code="ghd_hip_extension",
        category="gymnastics",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ghd hip extension", "ghd back extension"],
        muscles={"primary": ["Posterior"], "secondary": ["Core"]},
    ),
    mv(
        name="Back Extension",
        code="back_extension",
        category="gymnastics",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["back extension", "back extensions"],
        muscles={"primary": ["Posterior"], "secondary": ["Core"]},
    ),
    mv(
        name="Glute Bridge",
        code="glute_bridge",
        category="gymnastics",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["glute bridge", "hip bridge"],
        muscles={"primary": ["Posterior"], "secondary": ["Core"]},
    ),
    mv(
        name="Ring Support Hold",
        code="ring_support_hold",
        category="gymnastics",
        pattern="push",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["ring support hold", "ring support"],
        muscles={"primary": ["Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Ring Turned-Out Support",
        code="ring_turned_out_support",
        category="gymnastics",
        pattern="push",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["ring turned out support", "rto support"],
        muscles={"primary": ["Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Skin the Cat",
        code="skin_the_cat",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["skin the cat", "skin-the-cat"],
        muscles={"primary": ["Posterior", "Brazos"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Front Lever",
        code="front_lever",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["front lever", "front lever hold"],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Back Lever",
        code="back_lever",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["back lever", "back lever hold"],
        muscles={"primary": ["Posterior"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Hollow Hang",
        code="hollow_hang",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["hollow hang", "hollow hang hold"],
        muscles={"primary": ["Grip"], "secondary": ["Core", "Posterior"]},
    ),
    mv(
        name="Arch Hang",
        code="arch_hang",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["arch hang", "arch hang hold"],
        muscles={"primary": ["Grip"], "secondary": ["Posterior", "Core"]},
    ),
    mv(
        name="Tuck Hold",
        code="tuck_hold",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["tuck hold", "tuck hold position"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Wall Sit",
        code="wall_sit",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["wall sit", "wall sit hold"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="GHD Reverse Hyper",
        code="ghd_reverse_hyper",
        category="gymnastics",
        pattern="hinge",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["ghd reverse hyper", "reverse hyper"],
        muscles={"primary": ["Posterior"], "secondary": ["Core"]},
    ),
    mv(
        name="Seated Rope Pull",
        code="seated_rope_pull",
        category="gymnastics",
        pattern="pull",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["seated rope pull", "seated rope pulls"],
        muscles={"primary": ["Brazos", "Posterior"], "secondary": ["Core", "Grip"]},
    ),
    mv(
        name="Handstand Shoulder Tap",
        code="handstand_shoulder_tap",
        category="gymnastics",
        pattern="push",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["handstand shoulder tap", "hspu shoulder tap"],
        muscles={"primary": ["Hombros"], "secondary": ["Core", "Brazos"]},
    ),
    mv(
        name="Tuck Jump",
        code="tuck_jump",
        category="gymnastics",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["tuck jump", "tuck jumps"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Jumping Jack",
        code="jumping_jack",
        category="gymnastics",
        pattern="jump",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["jumping jack", "jumping jacks"],
        muscles={"primary": ["Piernas"], "secondary": ["Hombros", "Core"]},
    ),
    mv(
        name="Reverse Crunch",
        code="reverse_crunch",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["reverse crunch", "reverse crunches"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Knee Tuck",
        code="knee_tuck",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["knee tuck", "knee tucks"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Bird Dog",
        code="bird_dog",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["bird dog", "bird dogs"],
        muscles={"primary": ["Core"], "secondary": ["Posterior"]},
    ),
    mv(
        name="Curtsy Lunge",
        code="curtsy_lunge",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["curtsy lunge", "curtsy lunges"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Sumo Squat",
        code="sumo_squat",
        category="gymnastics",
        pattern="squat",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["sumo squat", "sumo air squat"],
        muscles={"primary": ["Piernas"], "secondary": ["Core"]},
    ),
    mv(
        name="Windshield Wiper",
        code="windshield_wiper",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["windshield wiper", "wipers"],
        muscles={"primary": ["Core"], "secondary": ["Grip", "Posterior"]},
    ),
    mv(
        name="Dragon Flag",
        code="dragon_flag",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["dragon flag", "dragon flags"],
        muscles={"primary": ["Core"], "secondary": ["Posterior"]},
    ),
    mv(
        name="V-Sit",
        code="v_sit",
        category="gymnastics",
        pattern="core",
        default_metric_unit="time",
        supports_flags=supports(time=True),
        aliases=["v sit", "v-sit"],
        muscles={"primary": ["Core"]},
    ),
    mv(
        name="Candlestick",
        code="candlestick",
        category="gymnastics",
        pattern="core",
        default_metric_unit="reps",
        supports_flags=supports(reps=True),
        aliases=["candlestick", "candlesticks"],
        muscles={"primary": ["Core"], "secondary": ["Posterior"]},
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


