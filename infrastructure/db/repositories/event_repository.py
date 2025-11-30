from sqlalchemy.orm import Session

from infrastructure.db.models import EventORM, UserEventORM, UserORM
from .base import BaseRepository


class EventRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, EventORM)

    def add_participant(self, event_id: int, user_id: int):
        link = UserEventORM(user_id=user_id, event_id=event_id)
        self.session.add(link)
        self.session.commit()
        return link

    def list_participants(self, event_id: int):
        return (
            self.session.query(UserORM)
            .join(UserEventORM, UserORM.id == UserEventORM.user_id)
            .filter(UserEventORM.event_id == event_id)
            .all()
        )
