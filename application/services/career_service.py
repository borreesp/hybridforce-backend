from datetime import datetime, timedelta
from typing import Dict, Optional

from infrastructure.db.models import AthleteLevelORM, UserProgressORM, UserTrainingLoadORM


class CareerService:
    def __init__(self, session):
        self.session = session

    def _levels(self):
        return (
            self.session.query(AthleteLevelORM)
            .order_by(AthleteLevelORM.sort_order.asc())
            .all()
        )

    def _ensure_progress(self, user_id: int) -> UserProgressORM:
        progress = self.session.get(UserProgressORM, user_id)
        if not progress:
            progress = UserProgressORM(user_id=user_id, xp_total=0, level=1, progress_pct=0)
            self.session.add(progress)
            self.session.flush()
        return progress

    def _compute_level(self, xp_total: int) -> Dict[str, Optional[int]]:
        levels = self._levels()
        current = levels[0] if levels else None
        next_level = None
        for idx, lvl in enumerate(levels):
            min_xp = lvl.min_xp or 0
            max_xp = lvl.max_xp or min_xp
            if xp_total < max_xp:
                current = lvl
                next_level = levels[idx + 1] if idx + 1 < len(levels) else None
                break
            current = lvl
            next_level = levels[idx + 1] if idx + 1 < len(levels) else None
        if not current:
            return {"level": 1, "next_level": None, "progress_pct": 0, "xp_to_next": None, "athlete_level_id": None}
        min_xp = current.min_xp or 0
        xp_span = (next_level.min_xp - min_xp) if next_level and next_level.min_xp is not None else None
        progress_pct = 100.0 if not xp_span or xp_span <= 0 else max(0.0, min(100.0, ((xp_total - min_xp) / xp_span) * 100))
        xp_to_next = (next_level.min_xp - xp_total) if next_level and next_level.min_xp is not None else None
        return {
            "level": current.sort_order or current.id,
            "athlete_level_id": current.id,
            "next_level": next_level.sort_order if next_level else None,
            "progress_pct": progress_pct,
            "xp_to_next": xp_to_next,
        }

    def add_xp(self, user_id: int, amount: int) -> Dict[str, object]:
        progress = self._ensure_progress(user_id)
        progress.xp_total += int(amount)
        snapshot = self._recalculate(progress)
        self.session.commit()
        return snapshot

    def recalculate_level(self, user_id: int) -> Dict[str, object]:
        progress = self._ensure_progress(user_id)
        snapshot = self._recalculate(progress)
        self.session.commit()
        return snapshot

    def _weekly_streak(self, user_id: int) -> int:
        seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
        count = (
            self.session.query(UserTrainingLoadORM)
            .filter(UserTrainingLoadORM.user_id == user_id, UserTrainingLoadORM.load_date >= seven_days_ago)
            .count()
        )
        return count

    def _recalculate(self, progress: UserProgressORM) -> Dict[str, object]:
        computed = self._compute_level(progress.xp_total)
        progress.level = computed["level"]
        progress.progress_pct = computed["progress_pct"]
        progress.updated_at = datetime.utcnow()
        if progress.user:
            progress.user.athlete_level_id = computed["athlete_level_id"]
        return {
            "user_id": progress.user_id,
            "xp_total": progress.xp_total,
            "level": progress.level,
            "progress_pct": progress.progress_pct,
            "next_level": computed["next_level"],
            "xp_to_next": computed["xp_to_next"],
            "weekly_streak": self._weekly_streak(progress.user_id),
            "updated_at": progress.updated_at,
        }

    def snapshot(self, user_id: int) -> Dict[str, object]:
        progress = self._ensure_progress(user_id)
        return self._recalculate(progress)
