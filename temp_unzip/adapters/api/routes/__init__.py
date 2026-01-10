from fastapi import APIRouter, Depends

from .users import router as users_router
from .workouts import router as workouts_router
from .equipment import router as equipment_router
from .events import router as events_router
from .training_plans import router as training_plans_router
from .workout_results import router as workout_results_router
from .lookups import router as lookups_router
from .movements import router as movements_router
from .auth import router as auth_router
from .athlete import router as athlete_router
from infrastructure.auth.dependencies import require_user

protected = [Depends(require_user)]
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"], dependencies=protected)
api_router.include_router(workouts_router, prefix="/workouts", tags=["workouts"], dependencies=protected)
api_router.include_router(equipment_router, prefix="/equipment", tags=["equipment"], dependencies=protected)
api_router.include_router(events_router, prefix="/events", tags=["events"], dependencies=protected)
api_router.include_router(training_plans_router, prefix="/training-plans", tags=["training-plans"], dependencies=protected)
api_router.include_router(workout_results_router, prefix="/workout-results", tags=["workout-results"], dependencies=protected)
api_router.include_router(lookups_router, prefix="/lookups", tags=["lookups"], dependencies=protected)
api_router.include_router(movements_router, prefix="/movements", tags=["movements"], dependencies=protected)
api_router.include_router(athlete_router, prefix="/athlete", tags=["athlete"], dependencies=protected)
