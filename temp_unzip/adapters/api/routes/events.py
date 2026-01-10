from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.events import EventCreate, EventUpdate, EventRead, EventParticipants
from application.schemas.users import UserRead
from application.services import EventService
from infrastructure.db.session import get_session

router = APIRouter()


@router.get("/", response_model=List[EventRead])
def list_events(session: Session = Depends(get_session)):
    service = EventService(session)
    return service.list()


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, session: Session = Depends(get_session)):
    service = EventService(session)
    return service.create(payload)


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: Session = Depends(get_session)):
    service = EventService(session)
    event = service.get(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, session: Session = Depends(get_session)):
    service = EventService(session)
    updated = service.update(event_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return updated


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, session: Session = Depends(get_session)):
    service = EventService(session)
    deleted = service.delete(event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return None


@router.get("/{event_id}/participants", response_model=EventParticipants)
def get_participants(event_id: int, session: Session = Depends(get_session)):
    service = EventService(session)
    event = service.get(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    participants = [UserRead.model_validate(user) for user in service.participants(event_id)]
    return EventParticipants(event=event, participants=participants)


@router.post("/{event_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_participant(event_id: int, user_id: int, session: Session = Depends(get_session)):
    service = EventService(session)
    link = service.add_participant(event_id, user_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event or user not found")
    return None
