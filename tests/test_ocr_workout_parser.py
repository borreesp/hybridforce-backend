import types

from application.services.ocr_workout_parser import parse_workout_text


def make_mv(idx, name):
    return types.SimpleNamespace(id=idx, name=name, default_load_unit=None, category=None)


def test_parse_intervals_abc_endurance():
    text = """ENDURANCE
4 RONDAS
2' ON 1' OFF
A) 20 CALS + MAX JUMPING LUNGES
B) 20 BURPEES TO PLATE + MAX KB SWINGS
C) 200M RUN + MAX BROAD JUMPS
"""
    movements = [
        make_mv(1, "AirBike"),
        make_mv(2, "Row"),
        make_mv(3, "Jumping Lunge"),
        make_mv(4, "Burpee to Plate"),
        make_mv(5, "Kettlebell Swing"),
        make_mv(6, "Run"),
        make_mv(7, "Broad Jump"),
    ]

    draft = parse_workout_text(text, movements)
    assert draft.detected_style == "intervals"
    assert draft.rounds == 4
    assert draft.work_seconds == 120
    assert draft.rest_seconds == 60
    assert len(draft.blocks) == 1
    block = draft.blocks[0]
    assert len(block.scenarios) == 3
    scenario_a = block.scenarios[0]
    assert scenario_a.label == "A"
    # first item is cals unresolved (no machine), second is jumping lunge resolved
    assert scenario_a.items[0].calories == 20
    assert scenario_a.items[1].movement_id == 3
    scenario_b = block.scenarios[1]
    assert scenario_b.items[0].movement_id == 4
    assert scenario_b.items[1].movement_id == 5
    scenario_c = block.scenarios[2]
    assert scenario_c.items[0].distance_meters == 200
    assert scenario_c.items[1].movement_id == 7


def test_parse_emom_basic():
    text = "EMOM 12: 5 deadlift + 10 wall balls"
    movements = [make_mv(1, "Deadlift"), make_mv(2, "Wall Ball")]
    draft = parse_workout_text(text, movements)
    assert draft.detected_style == "emom"
    assert draft.blocks[0].block_type == "emom"


def test_parse_for_time():
    text = "FOR TIME: 150 wall balls"
    movements = [make_mv(2, "Wall Ball")]
    draft = parse_workout_text(text, movements)
    assert draft.detected_style == "for_time"
    assert draft.blocks[0].scenarios[0].items[0].movement_id == 2


def test_unresolved_when_no_match():
    text = "AMRAP 10: 20 mysterious move"
    movements = []
    draft = parse_workout_text(text, movements)
    assert draft.unresolved


def test_calories_are_dropped_for_non_erg_movements():
    text = "AMRAP 10: 20 cal burpees"
    movements = [make_mv(1, "Burpee"), make_mv(2, "Row")]
    draft = parse_workout_text(text, movements)
    items = draft.blocks[0].scenarios[0].items
    # burpee was matched, but calories must be cleared because it's not an ERG
    assert items[0].movement_id == 1
    assert items[0].calories is None
