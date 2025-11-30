from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.training_plans import (
    TrainingPlanCreate,
    TrainingPlanUpdate,
    TrainingPlanRead,
    TrainingPlanDayRead,
)
from application.services import TrainingPlanService
from infrastructure.db.session import get_session

router = APIRouter()


@router.get("/", response_model=List[TrainingPlanRead])
def list_plans(session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    return service.list()


@router.post("/", response_model=TrainingPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(payload: TrainingPlanCreate, session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    plan = service.create(payload)
    return plan


@router.get("/{plan_id}", response_model=TrainingPlanRead)
def get_plan(plan_id: int, session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    plan = service.get(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training plan not found")
    return plan


@router.put("/{plan_id}", response_model=TrainingPlanRead)
def update_plan(plan_id: int, payload: TrainingPlanUpdate, session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    updated = service.update(plan_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training plan not found")
    return updated


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    deleted = service.delete(plan_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training plan not found")
    return None


@router.get("/{plan_id}/days", response_model=List[TrainingPlanDayRead])
def list_plan_days(plan_id: int, session: Session = Depends(get_session)):
    service = TrainingPlanService(session)
    plan = service.get(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training plan not found")
    return [TrainingPlanDayRead.model_validate(day) for day in service.list_days(plan_id)]
