import sqlite3
import types

from application.services.ocr_workout_parser import parse_workout_text


def normalize_alias(value: str) -> str:
    if not value:
        return ""
    text_value = value.lower().strip()
    text_value = text_value.replace("\u2013", "-").replace("\u2014", "-")
    for ch in ".,;:()[]{}'\"":
        text_value = text_value.replace(ch, " ")
    while "--" in text_value:
        text_value = text_value.replace("--", "-")
    text_value = "".join(ch if (ch.isalnum() or ch in {" ", "-"}) else " " for ch in text_value)
    text_value = " ".join(text_value.split())
    return text_value


def seed_minimal_catalog(conn: sqlite3.Connection):
    def get_or_create_movement(name: str, **fields):
        row = conn.execute("SELECT id, code FROM movements WHERE lower(name)=lower(?)", (name,)).fetchone()
        if row:
            updates = {}
            if fields.get("code") and not row[1]:
                updates["code"] = fields["code"]
            if updates:
                conn.execute("UPDATE movements SET code=:code WHERE lower(name)=lower(:name)", {"code": updates["code"], "name": name})
            return row[0]
        columns = ["name"] + list(fields.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = [name] + [fields[k] for k in fields.keys()]
        conn.execute(f"INSERT INTO movements ({', '.join(columns)}) VALUES ({placeholders})", values)
        return conn.execute("SELECT id FROM movements WHERE lower(name)=lower(?)", (name,)).fetchone()[0]

    def upsert_alias(movement_id: int, alias: str):
        alias_norm = normalize_alias(alias)
        exists = conn.execute(
            "SELECT 1 FROM movement_aliases WHERE movement_id=? AND alias_normalized=?",
            (movement_id, alias_norm),
        ).fetchone()
        if exists:
            return
        conn.execute(
            "INSERT INTO movement_aliases (movement_id, alias, alias_normalized, source) VALUES (?, ?, ?, ?)",
            (movement_id, alias, alias_norm, "import"),
        )

    row_id = get_or_create_movement(
        "Row",
        code="row",
        supports_reps=0,
        supports_load=0,
        supports_distance=1,
        supports_time=1,
        supports_calories=1,
    )
    upsert_alias(row_id, "20 cals")

    t2b_id = get_or_create_movement(
        "Toes-to-Bar",
        code="toes_to_bar",
        supports_reps=1,
        supports_load=0,
        supports_distance=0,
        supports_time=0,
        supports_calories=0,
    )
    upsert_alias(t2b_id, "t2b")

    conn.commit()
    return row_id, t2b_id


def test_aliases_map_and_idempotent_seed():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        CREATE TABLE movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT,
            supports_reps INTEGER NOT NULL DEFAULT 0,
            supports_load INTEGER NOT NULL DEFAULT 0,
            supports_distance INTEGER NOT NULL DEFAULT 0,
            supports_time INTEGER NOT NULL DEFAULT 0,
            supports_calories INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE movement_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movement_id INTEGER NOT NULL,
            alias TEXT NOT NULL,
            alias_normalized TEXT NOT NULL,
            source TEXT,
            UNIQUE (movement_id, alias_normalized)
        )
        """
    )

    row_id, t2b_id = seed_minimal_catalog(conn)
    seed_minimal_catalog(conn)

    movement_count = conn.execute("SELECT COUNT(*) FROM movements").fetchone()[0]
    alias_count = conn.execute("SELECT COUNT(*) FROM movement_aliases").fetchone()[0]
    assert movement_count == 2
    assert alias_count == 2

    alias_rows = conn.execute("SELECT movement_id, alias, alias_normalized FROM movement_aliases").fetchall()
    alias_map = {}
    for movement_id, alias, alias_normalized in alias_rows:
        alias_map.setdefault(movement_id, []).append(
            types.SimpleNamespace(alias=alias, alias_normalized=alias_normalized)
        )

    movements = []
    for movement_id, name in conn.execute("SELECT id, name FROM movements").fetchall():
        movements.append(types.SimpleNamespace(id=movement_id, name=name, aliases=alias_map.get(movement_id, [])))

    draft = parse_workout_text("TEST\\nA) 20 CALS", movements)
    assert draft.blocks[0].scenarios[0].items[0].movement_id == row_id

    draft = parse_workout_text("TEST\\nA) T2B", movements)
    assert draft.blocks[0].scenarios[0].items[0].movement_id == t2b_id
