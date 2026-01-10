# HybridForce API

FastAPI + SQLAlchemy stack with lookup-driven workout model (blocks, movimientos, versionado, cargas de usuario).

## Arranque rapido

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

- Configura `DATABASE_URL` y `CORS_ORIGINS` en `.env`.
- En `startup` se ejecuta el seeder (`infrastructure/db/seed.py`) para poblar lookups, 1 usuario demo y un workout con bloques/movimientos.

## Migraciones

- Alembic revision: `alembic/versions/20251130_01_new_schema.py` crea el ERD extendido (lookups, workouts versionados, bloques, movimientos, stats, training_load, capacity_profile...).
- Alembic revision: `alembic/versions/20251130_231109_auth_tokens.py` anade `token_version` para invalidar sesiones JWT en logout.
- Ejecuta `alembic upgrade head` antes de levantar la API en entornos existentes.

## Endpoints relevantes

- **Auth**: `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `/auth/me` (JWT corto + refresh en cookies HttpOnly SameSite=Lax; rate limit login 5/10min; `token_version` para invalidar).
- **Lookups**: `GET /lookups` devuelve tablas catalogo (athlete/intensity/energy/capacities/muscle/hyrox).
- **Workouts**: CRUD `/workouts`, estructura `GET /workouts/{id}/structure`, bloques `GET /workouts/{id}/blocks`, versiones `GET /workouts/{id}/versions`, stats `/workouts/stats`, analisis `/workouts/{id}/analysis`.
- **Movimientos**: CRUD `/movements` con musculos asociados.
- **Usuarios**: `GET /users/{id}/training-load`, `GET /users/{id}/capacity-profile` (filtrados por usuario autenticado), perfil/eventos/resultados.
- **Otros**: `/equipment`, `/events`, `/training-plans`, `/workout-results`.

## Estructura

- `adapters/api/routes/` routers FastAPI (auth protegido salvo rutas de autenticacion y health).
- `application/services/` orquesta repositorios y dominio.
- `infrastructure/db/models/` mapeos ORM.
- `infrastructure/db/repositories/` acceso a datos.
- `domain/` dataclasses para analisis de workouts.

## Seeds

`seed_data(session)` crea:
- Lookups (athlete/intensity/energy/capacities/muscle/hyrox).
- Usuario demo `lena@example.com` (password `changeme` hasheada) con carga y perfil de capacidades.
- Workout "Engine Builder" con bloques, movimientos, metadata y stats.
- Plan de training y evento HYROX demo.

## Notas de compatibilidad

- Los enums historicos se mantienen como `code` en las tablas lookup.
- Los endpoints antiguos conservan naming; se anaden campos nuevos de forma retrocompatible (`extra_attributes_json`, `blocks`, versionado).
