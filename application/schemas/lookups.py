from typing import List, Optional

from .base import ORMModel


class LookupItem(ORMModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    sort_order: Optional[int] = None


class LookupTables(ORMModel):
    athlete_levels: List[LookupItem] = []
    intensity_levels: List[LookupItem] = []
    energy_domains: List[LookupItem] = []
    physical_capacities: List[LookupItem] = []
    muscle_groups: List[LookupItem] = []
    hyrox_stations: List[LookupItem] = []
