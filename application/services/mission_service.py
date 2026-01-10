from datetime import datetime
from typing import List, Tuple

from infrastructure.db.models import MissionORM, UserMissionORM
from .career_service import CareerService


class MissionService:
    def __init__(self, session):
        self.session = session
        self.career_service = CareerService(session)

    def assign_active(self, user_id: int) -> List[UserMissionORM]:
        missions = self.session.query(MissionORM).filter(MissionORM.is_active.is_(True)).all()
        user_missions = (
            self.session.query(UserMissionORM)
            .filter(UserMissionORM.user_id == user_id)
            .all()
        )
        existing_ids = {um.mission_id for um in user_missions}
        for mission in missions:
            if mission.id in existing_ids:
                continue
            self.session.add(
                UserMissionORM(
                    user_id=user_id,
                    mission_id=mission.id,
                    status="assigned",
                    progress_value=0,
                )
            )
        self.session.flush()
        return (
            self.session.query(UserMissionORM)
            .filter(UserMissionORM.user_id == user_id)
            .all()
        )

    def _parse_target(self, mission: MissionORM) -> float:
        data = mission.condition_json or {}
        return float(data.get("target", 1))

    def _is_pr_required(self, mission: MissionORM) -> bool:
        data = mission.condition_json or {}
        return data.get("type") == "pr"

    def update_progress_for_workout(self, user_id: int, new_pr: bool = False) -> Tuple[List[str], int]:
        missions = self.assign_active(user_id)
        completed_names: List[str] = []
        total_xp = 0
        now = datetime.utcnow()
        for um in missions:
            if um.status in ("completed", "expired"):
                continue
            if um.expires_at and um.expires_at < now:
                um.status = "expired"
                continue
            mission = um.mission
            if not mission or not mission.is_active:
                continue
            if self._is_pr_required(mission) and not new_pr:
                continue
            um.progress_value += 1
            um.status = "in_progress"
            target = self._parse_target(mission)
            if um.progress_value >= target:
                um.status = "completed"
                um.completed_at = now
                completed_names.append(mission.title)
                total_xp += int(mission.xp_reward or 0)
        if total_xp > 0:
            self.career_service.add_xp(user_id, total_xp)
        self.session.commit()
        return completed_names, total_xp
