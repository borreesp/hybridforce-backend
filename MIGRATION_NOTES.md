### Migración a modelo relacional extendido (lookup tables + bloques + movimientos)

- Nuevo esquema con tablas de catálogo: `athlete_levels`, `intensity_levels`, `energy_domains`, `physical_capacities`, `muscle_groups`, `hyrox_stations` (todas con `code` único e índice en `sort_order` donde aplica).
- `workouts` ahora tiene versionado (`parent_workout_id`, `version`, `is_active`), FKs a lookups (`domain_id`, `intensity_level_id`, `hyrox_transfer_level_id`, `main_muscle_group_id`) y timestamps.
- Se separan `workout_metadata` y `workout_stats` (1:1) y se migran los datos previos.
- Nuevos agregados: `movements`, `movement_muscles`, `workout_blocks`, `workout_block_movements` (con `CHECK` de métricas y `UNIQUE` de posición), `user_training_load`, `user_capacity_profile`.
- Constraints clave: `similar_workouts` con `CHECK workout_id <> similar_workout_id` y orden estricto (`workout_id < similar_workout_id`); `workout_block`/`movement` posiciones únicas; `user_training_load` única por día; `user_capacity_profile` única por capacidad+timestamp.
- Migración Alembic: `alembic/versions/20251130_01_new_schema.py`
  - Crea lookups, pobla con valores de enums previos.
  - Añade columnas FK y migra valores de enums → lookups.
  - Genera tablas nuevas (metadata/stats, movimientos/bloques, cargas de usuario).
  - Elimina columnas antiguas basadas en enums y tipos ENUM.
- Arranque: `main.py` ejecuta `alembic upgrade head` en el startup antes del seeding (`infrastructure/db/seed.py`).
- Seeds: `seed.py` rellena lookups si están vacíos y crea datos mock con workout, plan, event, movimientos/bloques.

**Pasos para aplicar en entornos existentes**
1. Ajusta `.env` con el `DATABASE_URL` real.
2. Ejecuta migración: `alembic upgrade head` (o arranca la app y deja que lo haga en startup).
3. Verifica tablas nuevas y datos de catálogo.
4. Si hay client apps que lean enums, ahora deben resolver/mostrar `code` de lookups (el API sigue devolviendo los códigos originales).
