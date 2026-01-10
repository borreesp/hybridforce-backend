from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.users import UserCreate, UserUpdate, UserRead, UserProfile
from application.schemas.user_metrics import UserTrainingLoadRead, UserCapacityProfileRead, UserCapacityProfileResponse
from application.schemas.events import EventRead
from application.schemas.results import WorkoutResultRead
from application.services import UserService
from infrastructure.db.session import get_session
from infrastructure.auth.dependencies import get_current_user
from infrastructure.db.models import UserORM

router = APIRouter()


def _user_to_read(user: UserORM) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        athlete_level=getattr(user.athlete_level, "code", None),
    )


@router.get("/", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)):
    service = UserService(session)
    return [_user_to_read(u) for u in service.list()]


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    service = UserService(session)
    created = service.create(payload)
    return _user_to_read(created)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    service = UserService(session)
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_read(user)


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, session: Session = Depends(get_session)):
    service = UserService(session)
    updated = service.update(user_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_read(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    service = UserService(session)
    deleted = service.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None


@router.get("/{user_id}/profile", response_model=UserProfile)
def user_profile(user_id: int, session: Session = Depends(get_session), current=Depends(get_current_user)):
    if current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    service = UserService(session)
    profile = service.profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = profile["user"]
    events = [EventRead.model_validate(event) for event in profile["events"]]
    results = [WorkoutResultRead.model_validate(result) for result in profile["results"]]
    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        athlete_level=getattr(user.athlete_level, "code", None),
        events=events,
        results=results,
    )


@router.get("/{user_id}/events", response_model=List[EventRead])
def user_events(user_id: int, session: Session = Depends(get_session), current=Depends(get_current_user)):
    if current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    service = UserService(session)
    profile = service.profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return [EventRead.model_validate(event) for event in profile["events"]]


@router.get("/{user_id}/training-load", response_model=List[UserTrainingLoadRead])
def user_training_load(user_id: int, session: Session = Depends(get_session), current=Depends(get_current_user)):
    if current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    service = UserService(session)
    loads = service.training_load(user_id)
    if loads is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return [UserTrainingLoadRead.model_validate(item) for item in loads]


@router.get("/{user_id}/capacity-profile", response_model=UserCapacityProfileResponse)
def user_capacity_profile(user_id: int, session: Session = Depends(get_session), current=Depends(get_current_user)):
    if current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    service = UserService(session)
    capacities = service.capacity_profile(user_id)
    if capacities is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserCapacityProfileResponse(
        user_id=user_id,
        capacities=[
            UserCapacityProfileRead(
                id=item.id,
                user_id=item.user_id,
                capacity_code=item.capacity.code if item.capacity else "",
                capacity_name=item.capacity.name if item.capacity else None,
                value=item.value,
                measured_at=item.measured_at,
            )
            for item in capacities
        ],
    )
