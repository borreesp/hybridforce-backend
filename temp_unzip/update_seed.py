# -*- coding: utf-8 -*-
from pathlib import Path
path = Path('infrastructure/db/seed.py')
text = path.read_text(encoding='utf-8')
old = """    hyrox_race.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_race.id,
        volume_total=\"3km run + 1500m row + 75 wall balls\",
        work_rest_ratio=\"Trabajo continuo\",
        dominant_stimulus=\"Mixto (cardio + estaciones HYROX)\",
        load_type=\"Bodyweight/mediana carga\",
        athlete_profile_desc=\"Atleta que ya ha hecho o quiere hacer HYROX individual.\",
        target_athlete_desc=\"Preparar sensaci\u00f3n de 'race pace' pero en formato corto.\",
        pacing_tip=\"Ritmo de carrera ligeramente m\u00e1s suave que ritmo de 1km en competici\u00f3n.\",
        pacing_detail=\"Usar carrera para recuperar respiraci\u00f3n y remar a ritmo estable.\",
        break_tip=\"Wall balls en series de 15-15-10-10-10 con respiraci\u00f3n controlada.\",
        rx_variant=\"Run 1km / row moderado / WB 9/6kg.\",
        scaled_variant=\"Run 800m / row 300m / WB 6/4kg (total 60 reps).\",
        ai_observation=\"WOD perfecto para testear c\u00f3mo se comporta el atleta con bloques largos de carrera + estaci\u00f3n.\",
        session_load=\"High\",
        session_feel=\"Sensaci\u00f3n de mini carrera HYROX.\",
    )"""
new = """    hyrox_race.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_race.id,
        **_sanitize_metadata({
            'volume_total': '3km run + 1500m row + 75 wall balls',
            'work_rest_ratio': 'Trabajo continuo',
            'dominant_stimulus': 'Mixto (cardio + estaciones HYROX)',
            'load_type': 'Bodyweight/mediana carga',
            'session_load': 'High',
        }),
        athlete_profile_desc=\"Atleta que ya ha hecho o quiere hacer HYROX individual.\",
        target_athlete_desc=\"Preparar sensaci\u00f3n de 'race pace' pero en formato corto.\",
        pacing_tip=\"Ritmo de carrera ligeramente m\u00e1s suave que ritmo de 1km en competici\u00f3n.\",
        pacing_detail=\"Usar carrera para recuperar respiraci\u00f3n y remar a ritmo estable.\",
        break_tip=\"Wall balls en series de 15-15-10-10-10 con respiraci\u00f3n controlada.\",
        rx_variant=\"Run 1km / row moderado / WB 9/6kg.\",
        scaled_variant=\"Run 800m / row 300m / WB 6/4kg (total 60 reps).\",
        ai_observation=\"WOD perfecto para testear c\u00f3mo se comporta el atleta con bloques largos de carrera + estaci\u00f3n.\",
        session_feel=\"Sensaci\u00f3n de mini carrera HYROX.\",
    )"""
old2 = """    hyrox_sled.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_sled.id,
        volume_total=\"2km run aprox + 100 lunges + 50 BBJO\",
        work_rest_ratio=\"Intervalo denso\",
        dominant_stimulus=\"Metcon pesado de piernas\",
        load_type=\"KB/propio cuerpo\",
        athlete_profile_desc=\"Atleta que sufre con sled push/pull y necesita m\u00e1s fuerza-resistencia de pierna.\",
        target_athlete_desc=\"Mejorar tolerancia a lactato en piernas.\",
        pacing_tip=\"Las dos primeras rondas deben sentirse m\u00e1s lentas de lo que te gustar\u00eda.\",
        pacing_detail=\"Correr suave, lunges controlados y BBJO en bloques de 5.\",
        break_tip=\"Respiraciones profundas al terminar lunges antes de empezar BBJO.\",
        rx_variant=\"Run 400m / KB 24/16kg / BBJO est\u00e1ndar.\",
        scaled_variant=\"Run 300m / KB 16/12kg / burpees normales.\",
        ai_observation=\"Simula muy bien el patr\u00f3n sensaci\u00f3n de sled: piernas hinchadas y pulm\u00f3n alto.\",
        session_load=\"High\",
        session_feel=\"Piernas ardiendo, respiraci\u00f3n alta.\",
    )"""
new2 = """    hyrox_sled.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_sled.id,
        **_sanitize_metadata({
            'volume_total': '2km run aprox + 100 lunges + 50 BBJO',
            'work_rest_ratio': 'Intervalo denso',
            'dominant_stimulus': 'Metcon pesado de piernas',
            'load_type': 'KB/propio cuerpo',
            'session_load': 'High',
        }),
        athlete_profile_desc=\"Atleta que sufre con sled push/pull y necesita m\u00e1s fuerza-resistencia de pierna.\",
        target_athlete_desc=\"Mejorar tolerancia a lactato en piernas.\",
        pacing_tip=\"Las dos primeras rondas deben sentirse m\u00e1s lentas de lo que te gustar\u00eda.\",
        pacing_detail=\"Correr suave, lunges controlados y BBJO en bloques de 5.\",
        break_tip=\"Respiraciones profundas al terminar lunges antes de empezar BBJO.\",
        rx_variant=\"Run 400m / KB 24/16kg / BBJO est\u00e1ndar.\",
        scaled_variant=\"Run 300m / KB 16/12kg / burpees normales.\",
        ai_observation=\"Simula muy bien el patr\u00f3n sensaci\u00f3n de sled: piernas hinchadas y pulm\u00f3n alto.\",
        session_feel=\"Piernas ardiendo, respiraci\u00f3n alta.\",
    )"""
if old not in text:
    raise SystemExit('hyrox block missing')
if old2 not in text:
    raise SystemExit('hyrox sled block missing')
text = text.replace(old, new, 1)
text = text.replace(old2, new2, 1)
path.write_text(text, encoding='utf-8')
