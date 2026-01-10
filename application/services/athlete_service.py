from typing import List

from sqlalchemy import func

from infrastructure.db.models import (
    UserORM,
    UserCapacityProfileORM,
    UserSkillORM,
    UserBiometricORM,
    UserPROM,
    UserTrainingLoadORM,
    GlobalCapacityBenchmarkORM,
)
from .career_service import CareerService
from .achievement_service import AchievementService
from .mission_service import MissionService


class AthleteService:
    def __init__(self, session):
        self.session = session
        self.career_service = CareerService(session)
        self.achievement_service = AchievementService(session)
        self.mission_service = MissionService(session)

    def _latest_biometrics(self, user_id: int):
        return (
            self.session.query(UserBiometricORM)
            .filter(UserBiometricORM.user_id == user_id)
            .order_by(UserBiometricORM.measured_at.desc())
            .first()
        )

    def _latest_training_load(self, user_id: int):
        return (
            self.session.query(UserTrainingLoadORM)
            .filter(UserTrainingLoadORM.user_id == user_id)
            .order_by(UserTrainingLoadORM.load_date.desc())
            .all()
        )

    def _latest_capacity(self, user_id: int) -> List[UserCapacityProfileORM]:
        sub = (
            self.session.query(
                UserCapacityProfileORM.capacity_id,
                func.max(UserCapacityProfileORM.measured_at).label("max_date"),
            )
            .filter(UserCapacityProfileORM.user_id == user_id)
            .group_by(UserCapacityProfileORM.capacity_id)
            .subquery()
        )
        return (
            self.session.query(UserCapacityProfileORM)
            .join(
                sub,
                (UserCapacityProfileORM.capacity_id == sub.c.capacity_id)
                & (UserCapacityProfileORM.measured_at == sub.c.max_date),
            )
            .all()
        )

    def _skills(self, user_id: int):
        return (
            self.session.query(UserSkillORM)
            .filter(UserSkillORM.user_id == user_id)
            .order_by(UserSkillORM.measured_at.desc())
            .limit(10)
            .all()
        )

    def _prs(self, user_id: int):
        return (
            self.session.query(UserPROM)
            .filter(UserPROM.user_id == user_id)
            .order_by(UserPROM.achieved_at.desc())
            .limit(10)
            .all()
        )

    def _benchmarks(self, user_level_id: int):
        rows = (
            self.session.query(GlobalCapacityBenchmarkORM)
            .filter(GlobalCapacityBenchmarkORM.athlete_level_id == user_level_id)
            .all()
        )
        return rows

    def profile(self, user_id: int) -> dict:
        user: UserORM = self.session.get(UserORM, user_id)
        career = self.career_service.snapshot(user_id)
        biometrics = self._latest_biometrics(user_id)
        training_load = self._latest_training_load(user_id)
        capacities = self._latest_capacity(user_id)
        skills = self._skills(user_id)
        prs = self._prs(user_id)
        missions = self.mission_service.assign_active(user_id)
        benchmarks = self._benchmarks(user.athlete_level_id) if user else []

        return {
            "user_id": user_id,
            "career": career,
            "biometrics": biometrics,
            "training_load": training_load,
            "capacities": capacities,
            "skills": skills,
            "prs": prs,
            "missions": missions,
            "benchmarks": benchmarks,
        }
