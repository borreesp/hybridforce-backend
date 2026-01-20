"""Seed extended movements catalog (CrossFit + Hybrid/Hyrox)

Revision ID: 20260205_moves_ext
Revises: 20260205_01_drop_unused_tables
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "20260205_moves_ext"
down_revision = "20260205_01_drop_unused_tables"
branch_labels = None
depends_on = None


MOVEMENTS = [
    { "name": "Back Squat", "category": "Strength", "description": "Back squat con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Front Squat", "category": "Strength", "description": "Front squat con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Overhead Squat", "category": "Halterofilia", "description": "Overhead squat con barra (técnica/movilidad)", "default_load_unit": "kg", "video_url": None },

    { "name": "Clean", "category": "Halterofilia", "description": "Clean (cargada) con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Power Clean", "category": "Halterofilia", "description": "Power clean con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Squat Clean", "category": "Halterofilia", "description": "Squat clean con barra", "default_load_unit": "kg", "video_url": None },

    { "name": "Jerk", "category": "Halterofilia", "description": "Jerk con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Push Jerk", "category": "Halterofilia", "description": "Push jerk con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Clean & Jerk", "category": "Halterofilia", "description": "Clean & Jerk con barra", "default_load_unit": "kg", "video_url": None },

    { "name": "Snatch", "category": "Halterofilia", "description": "Snatch (arrancada) con barra", "default_load_unit": "kg", "video_url": None },
    { "name": "Power Snatch", "category": "Halterofilia", "description": "Power snatch con barra", "default_load_unit": "kg", "video_url": None },

    { "name": "Toes-to-Bar", "category": "Gimnásticos", "description": "Toes-to-bar en barra", "default_load_unit": None, "video_url": None },
    { "name": "Chest-to-Bar", "category": "Gimnásticos", "description": "Chest-to-bar pull-up", "default_load_unit": None, "video_url": None },
    { "name": "Handstand Push-up", "category": "Gimnásticos", "description": "Flexión en pino (HSPU)", "default_load_unit": None, "video_url": None },
    { "name": "Handstand Walk", "category": "Gimnásticos", "description": "Caminata en pino", "default_load_unit": None, "video_url": None },
    { "name": "Ring Dip", "category": "Gimnásticos", "description": "Fondos en anillas", "default_load_unit": None, "video_url": None },
    { "name": "Bar Muscle-Up", "category": "Gimnásticos", "description": "Muscle-up en barra", "default_load_unit": None, "video_url": None },
    { "name": "Ring Muscle-Up", "category": "Gimnásticos", "description": "Muscle-up en anillas", "default_load_unit": None, "video_url": None },
    { "name": "Rope Climb", "category": "Gimnásticos", "description": "Trepa de cuerda", "default_load_unit": None, "video_url": None },
    { "name": "Pistol Squat", "category": "Gimnásticos", "description": "Sentadilla a una pierna (pistol)", "default_load_unit": None, "video_url": None },

    { "name": "SkiErg", "category": "Cardio", "description": "SkiErg", "default_load_unit": None, "video_url": None },
    { "name": "BikeErg", "category": "Cardio", "description": "BikeErg", "default_load_unit": None, "video_url": None },
    { "name": "AirBike", "category": "Cardio", "description": "Bicicleta de aire (Assault)", "default_load_unit": None, "video_url": None },

    { "name": "Farmer Carry", "category": "Hybrid", "description": "Paseo del granjero (carga en manos)", "default_load_unit": "kg", "video_url": None },
    { "name": "Sandbag Carry", "category": "Hybrid", "description": "Transporte de saco (sandbag)", "default_load_unit": "kg", "video_url": None },
    { "name": "Sled Push", "category": "Hybrid", "description": "Empuje de trineo", "default_load_unit": "kg", "video_url": None },
    { "name": "Sled Pull", "category": "Hybrid", "description": "Arrastre de trineo", "default_load_unit": "kg", "video_url": None },

    { "name": "Dumbbell Snatch", "category": "Metcon", "description": "Snatch con mancuerna", "default_load_unit": "kg", "video_url": None },
    { "name": "Dumbbell Clean & Jerk", "category": "Metcon", "description": "Clean & Jerk con mancuerna", "default_load_unit": "kg", "video_url": None },
    { "name": "Devil's Press", "category": "Metcon", "description": "Devil's press con mancuernas", "default_load_unit": "kg", "video_url": None },
    { "name": "Wall Walk", "category": "Gimnásticos", "description": "Wall walk", "default_load_unit": None, "video_url": None },
    { "name": "Turkish Get-Up", "category": "Metcon", "description": "Turkish get-up con kettlebell", "default_load_unit": "kg", "video_url": None },

    { "name": "GHD Sit-up", "category": "Gimnásticos", "description": "Abdominal en GHD", "default_load_unit": None, "video_url": None },
    { "name": "Bear Crawl", "category": "Metcon", "description": "Gateo de oso", "default_load_unit": None, "video_url": None }
]


def _find_existing(conn, name: str):
    return conn.execute(text("SELECT id, category, description, default_load_unit, video_url FROM movements WHERE lower(name)=lower(:name)"), {"name": name}).fetchone()


def upgrade():
    conn = op.get_bind()
    inserted = 0
    updated = 0
    skipped = 0

    for item in MOVEMENTS:
        existing = _find_existing(conn, item["name"])
        if not existing:
            conn.execute(
                text(
                    "INSERT INTO movements (name, category, description, default_load_unit, video_url) "
                    "VALUES (:name, :category, :description, :default_load_unit, :video_url)"
                ),
                item,
            )
            inserted += 1
            continue

        updates = {}
        if not existing.category and item["category"]:
            updates["category"] = item["category"]
        if (not existing.description or existing.description.strip() == "") and item["description"]:
            updates["description"] = item["description"]
        if existing.default_load_unit is None and item["default_load_unit"]:
            updates["default_load_unit"] = item["default_load_unit"]
        if existing.video_url is None and item["video_url"]:
            updates["video_url"] = item["video_url"]

        if updates:
            conn.execute(
                text(
                    "UPDATE movements SET "
                    + ", ".join(f"{k}=:{k}" for k in updates.keys())
                    + " WHERE lower(name)=lower(:name)"
                ),
                {**updates, "name": item["name"]},
            )
            updated += 1
        else:
            skipped += 1

    op.execute(text("COMMIT"))
    print(f"[seed_movements_extended] inserted={inserted} updated={updated} skipped={skipped}")


def downgrade():
    # No borramos los movimientos para no romper datos existentes
    pass
