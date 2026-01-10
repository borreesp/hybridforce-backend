from typing import List, Optional

from .base import ORMModel
from .users import UserRead


class EventBase(ORMModel):
    name: str
    date: str
    location: str
    type: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(ORMModel):
    name: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None


class EventRead(EventBase):
    id: int


class EventParticipants(ORMModel):
    event: EventRead
    participants: List[UserRead]
