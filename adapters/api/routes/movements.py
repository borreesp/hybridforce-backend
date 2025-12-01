from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.movements import MovementRead, MovementCreate, MovementUpdate, MovementMuscleSchema
from application.services import MovementService
from infrastructure.db.session import get_session

router = APIRouter()


def _to_read_model(movement) -> MovementRead:
    return MovementRead(
        id=movement.id,
        name=movement.name,
        category=movement.category,
        description=movement.description,
        default_load_unit=movement.default_load_unit,
        video_url=movement.video_url,
        muscles=[
            MovementMuscleSchema(muscle_group=mm.muscle_group.code if mm.muscle_group else "", is_primary=mm.is_primary)
            for mm in movement.muscles
        ],
    )


@router.get("/", response_model=List[MovementRead])
def list_movements(session: Session = Depends(get_session)):
    service = MovementService(session)
    return [_to_read_model(m) for m in service.list()]


@router.get("/{movement_id}", response_model=MovementRead)
def get_movement(movement_id: int, session: Session = Depends(get_session)):
    service = MovementService(session)
    movement = service.get(movement_id)
    if not movement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found")
    return _to_read_model(movement)


@router.post("/", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_movement(payload: MovementCreate, session: Session = Depends(get_session)):
    service = MovementService(session)
    movement = service.create(payload)
    return _to_read_model(movement)


@router.put("/{movement_id}", response_model=MovementRead)
def update_movement(movement_id: int, payload: MovementUpdate, session: Session = Depends(get_session)):
    service = MovementService(session)
    movement = service.update(movement_id, payload)
    if not movement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found")
    return _to_read_model(movement)
