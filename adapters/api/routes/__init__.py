from fastapi import APIRouter

from .users import router as users_router
from .workouts import router as workouts_router
from .equipment import router as equipment_router
from .events import router as events_router
from .training_plans import router as training_plans_router
from .workout_results import router as workout_results_router

api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(workouts_router, prefix="/workouts", tags=["workouts"])
api_router.include_router(equipment_router, prefix="/equipment", tags=["equipment"])
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(training_plans_router, prefix="/training-plans", tags=["training-plans"])
api_router.include_router(workout_results_router, prefix="/workout-results", tags=["workout-results"])
