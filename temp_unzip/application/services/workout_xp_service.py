from datetime import datetime, timedelta
from typing import Optional, Tuple

from infrastructure.db.models import WorkoutORM, WorkoutResultORM
from infrastructure.db.repositories import WorkoutResultRepository
from .career_service import CareerService


class WorkoutXPService:
    def __init__(self, session):
        self.session = session
        self.result_repo = WorkoutResultRepository(session)
        self.career_service = CareerService(session)

    def _session_load_score(self, session_load: Optional[str]) -> int:
        mapping = {
            "low": 5,
            "light": 5,
            "moderate": 12,
            "medium": 12,
            "high": 18,
            "hard": 18,
        }
        if not session_load:
            return 8
        return mapping.get(session_load.lower(), 10)

    def _weekly_streak(self, user_id: int) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        return (
            self.session.query(WorkoutResultORM)
            .filter(WorkoutResultORM.user_id == user_id, WorkoutResultORM.created_at >= week_ago)
            .count()
        )

    def _improvement_bonus(self, user_id: int, workout_id: int, current_time: Optional[int]) -> int:
        if current_time is None:
            return 0
        previous = self.result_repo.latest_for_user_workout(user_id, workout_id)
        if not previous or not previous.time_seconds or previous.time_seconds <= 0:
            return 0
        delta = previous.time_seconds - current_time
        if delta <= 0:
            return 0
        improvement_pct = min(0.5, delta / previous.time_seconds)
        return int(20 + improvement_pct * 60)

    def compute_xp(self, user_id: int, workout_id: int, time_seconds: Optional[int], difficulty: Optional[int]) -> int:
        workout = self.session.get(WorkoutORM, workout_id)
        base = 25
        difficulty_score = difficulty or (workout.stats.estimated_difficulty if workout and workout.stats else 5) or 5
        session_load = workout.metadata_rel.session_load if workout and workout.metadata_rel else None
        session_load_score = self._session_load_score(session_load)
        improvement_bonus = self._improvement_bonus(user_id, workout_id, time_seconds)
        streak = self._weekly_streak(user_id)
        streak_bonus = min(40, streak * 5)
        total = base + int(difficulty_score * 10) + session_load_score + improvement_bonus + streak_bonus
        return max(15, total)

    def award_for_result(self, user_id: int, workout_id: int, time_seconds: Optional[int], difficulty: Optional[int]) -> Tuple[int, dict]:
        xp = self.compute_xp(user_id, workout_id, time_seconds, difficulty)
        snapshot = self.career_service.add_xp(user_id, xp)
        return xp, snapshot
