from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.results import WorkoutResultCreate, WorkoutResultUpdate, WorkoutResultRead
from application.services import WorkoutResultService
from infrastructure.db.session import get_session

router = APIRouter()


@router.get("/", response_model=List[WorkoutResultRead])
def list_results(session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    return service.list()


@router.post("/", response_model=WorkoutResultRead, status_code=status.HTTP_201_CREATED)
def create_result(payload: WorkoutResultCreate, session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    created = service.create(payload)
    if not created:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or workout not found")
    return created


@router.get("/workout/{workout_id}", response_model=List[WorkoutResultRead])
def results_for_workout(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    return service.by_workout(workout_id)


@router.get("/{result_id}", response_model=WorkoutResultRead)
def get_result(result_id: int, session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    result = service.get(result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    return result


@router.put("/{result_id}", response_model=WorkoutResultRead)
def update_result(result_id: int, payload: WorkoutResultUpdate, session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    updated = service.update(result_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    return updated


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, session: Session = Depends(get_session)):
    service = WorkoutResultService(session)
    deleted = service.delete(result_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    return None
