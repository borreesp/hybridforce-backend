from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.lookups import LookupTables, LookupItem
from application.services import LookupService
from infrastructure.db.session import get_session

router = APIRouter()


def _map(items):
    return [LookupItem.model_validate(item) for item in items]


@router.get("/", response_model=LookupTables)
def list_lookup_tables(session: Session = Depends(get_session)):
    service = LookupService(session)
    data = service.all()
    return LookupTables(
        athlete_levels=_map(data["athlete_levels"]),
        intensity_levels=_map(data["intensity_levels"]),
        energy_domains=_map(data["energy_domains"]),
        physical_capacities=_map(data["physical_capacities"]),
        muscle_groups=_map(data["muscle_groups"]),
        hyrox_stations=_map(data["hyrox_stations"]),
    )
