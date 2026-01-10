from typing import Optional

from application.schemas.users import UserCreate, UserUpdate
from domain.models.enums import AthleteLevel
from infrastructure.db.models import AthleteLevelORM, UserORM, EventORM, UserEventORM
from infrastructure.db.repositories import (
    UserRepository,
    EventRepository,
    WorkoutResultRepository,
    UserTrainingLoadRepository,
    UserCapacityProfileRepository,
)
from infrastructure.auth.security import hash_password


class UserService:
    def __init__(self, session):
        self.session = session
        self.repo = UserRepository(session)
        self.event_repo = EventRepository(session)
        self.result_repo = WorkoutResultRepository(session)
        self.training_repo = UserTrainingLoadRepository(session)
        self.capacity_repo = UserCapacityProfileRepository(session)

    def list(self):
        return self.repo.list()

    def get(self, user_id: int) -> Optional[UserORM]:
        return self.repo.get(user_id)

    def create(self, data: UserCreate):
        payload = self._prepare_payload(data.model_dump())
        payload["password"] = hash_password(payload["password"])
        return self.repo.create(**payload)

    def update(self, user_id: int, data: UserUpdate):
        user = self.repo.get(user_id)
        if not user:
            return None
        payload = self._prepare_payload(data.model_dump(exclude_none=True))
        if "password" in payload:
            payload["password"] = hash_password(payload["password"])
        return self.repo.update(user, **payload)

    def delete(self, user_id: int):
        user = self.repo.get(user_id)
        if not user:
            return None
        return self.repo.delete(user)

    def profile(self, user_id: int):
        user = self.repo.get(user_id)
        if not user:
            return None
        events = (
            self.session.query(EventORM)
            .join(UserEventORM, EventORM.id == UserEventORM.event_id)
            .filter(UserEventORM.user_id == user_id)
            .all()
        )
        results = self.result_repo.list_by_user(user_id)
        return {"user": user, "events": events, "results": results}

    def training_load(self, user_id: int):
        if not self.repo.get(user_id):
            return None
        return self.training_repo.list_for_user(user_id)

    def capacity_profile(self, user_id: int):
        if not self.repo.get(user_id):
            return None
        return self.capacity_repo.list_for_user(user_id)

    def _prepare_payload(self, payload: dict) -> dict:
        level = payload.pop("athlete_level", None)
        if "email" in payload and payload["email"]:
            payload["email"] = payload["email"].lower()
        if level:
            code = level if isinstance(level, str) else getattr(level, "value", level)
            level_row = self.session.query(AthleteLevelORM).filter(AthleteLevelORM.code == code).first()
            payload["athlete_level_id"] = level_row.id if level_row else None
        return payload
