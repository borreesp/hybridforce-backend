from typing import Optional

from application.schemas.events import EventCreate, EventUpdate
from infrastructure.db.repositories import EventRepository, UserRepository
from infrastructure.db.models import EventORM


class EventService:
    def __init__(self, session):
        self.repo = EventRepository(session)
        self.user_repo = UserRepository(session)

    def list(self):
        return self.repo.list()

    def get(self, event_id: int) -> Optional[EventORM]:
        return self.repo.get(event_id)

    def create(self, data: EventCreate):
        return self.repo.create(**data.model_dump())

    def update(self, event_id: int, data: EventUpdate):
        event = self.repo.get(event_id)
        if not event:
            return None
        payload = data.model_dump(exclude_none=True)
        return self.repo.update(event, **payload)

    def delete(self, event_id: int):
        event = self.repo.get(event_id)
        if not event:
            return None
        return self.repo.delete(event)

    def add_participant(self, event_id: int, user_id: int):
        if not self.repo.get(event_id) or not self.user_repo.get(user_id):
            return None
        return self.repo.add_participant(event_id, user_id)

    def participants(self, event_id: int):
        return self.repo.list_participants(event_id)
