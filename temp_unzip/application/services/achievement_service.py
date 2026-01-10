from datetime import datetime
from typing import List

from infrastructure.db.models import AchievementORM, UserAchievementORM
from .career_service import CareerService


class AchievementService:
    def __init__(self, session):
        self.session = session
        self.career_service = CareerService(session)

    def _user_has(self, user_id: int, achievement_id: int) -> bool:
        return (
            self.session.query(UserAchievementORM)
            .filter(UserAchievementORM.user_id == user_id, UserAchievementORM.achievement_id == achievement_id)
            .first()
            is not None
        )

    def unlock(self, user_id: int, achievement: AchievementORM) -> bool:
        if self._user_has(user_id, achievement.id):
            return False
        self.session.add(UserAchievementORM(user_id=user_id, achievement_id=achievement.id, unlocked_at=datetime.utcnow()))
        self.career_service.add_xp(user_id, int(achievement.xp_reward or 0))
        return True

    def evaluate_level(self, user_id: int, level: int) -> List[str]:
        achievements = (
            self.session.query(AchievementORM)
            .filter(AchievementORM.code.like("LEVEL_%"), AchievementORM.is_active.is_(True))
            .all()
        )
        unlocked: List[str] = []
        for ach in achievements:
            try:
                target = int(ach.code.split("_")[1])
            except (IndexError, ValueError):
                continue
            if level >= target and self.unlock(user_id, ach):
                unlocked.append(ach.name)
        self.session.commit()
        return unlocked

    def unlock_first_pr(self, user_id: int) -> List[str]:
        ach = (
            self.session.query(AchievementORM)
            .filter(AchievementORM.code == "FIRST_PR", AchievementORM.is_active.is_(True))
            .first()
        )
        if ach and self.unlock(user_id, ach):
            self.session.commit()
            return [ach.name]
        return []
