from sqlalchemy.orm import Session

from infrastructure.db.models import (
    AthleteLevelORM,
    EnergyDomainORM,
    IntensityLevelORM,
    PhysicalCapacityORM,
    MuscleGroupORM,
    HyroxStationORM,
)


class LookupRepository:
    def __init__(self, session: Session):
        self.session = session

    def all(self):
        return {
            "athlete_levels": self._ordered(AthleteLevelORM, AthleteLevelORM.sort_order),
            "intensity_levels": self._ordered(IntensityLevelORM, IntensityLevelORM.sort_order),
            "energy_domains": self._ordered(EnergyDomainORM),
            "physical_capacities": self._ordered(PhysicalCapacityORM),
            "muscle_groups": self._ordered(MuscleGroupORM),
            "hyrox_stations": self._ordered(HyroxStationORM),
        }

    def _ordered(self, model, sort_column=None):
        query = self.session.query(model)
        if sort_column is not None:
            query = query.order_by(sort_column)
        return query.all()
