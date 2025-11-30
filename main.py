import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.api.routes import api_router
from adapters.api.routes.workouts import analysis_router
from infrastructure.db.session import SessionLocal
from infrastructure.db.seed import seed_data

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "HybridForce API"))


def _get_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",")]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    with SessionLocal() as session:
        seed_data(session)


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": app.title}


app.include_router(api_router)
app.include_router(analysis_router)
