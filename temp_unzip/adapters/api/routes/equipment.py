from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.schemas.equipment import EquipmentCreate, EquipmentUpdate, EquipmentRead
from application.services import EquipmentService
from infrastructure.db.session import get_session

router = APIRouter()


@router.get("/", response_model=List[EquipmentRead])
def list_equipment(session: Session = Depends(get_session)):
    service = EquipmentService(session)
    return service.list()


@router.post("/", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate, session: Session = Depends(get_session)):
    service = EquipmentService(session)
    return service.create(payload)


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, session: Session = Depends(get_session)):
    service = EquipmentService(session)
    equipment = service.get(equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return equipment


@router.put("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(equipment_id: int, payload: EquipmentUpdate, session: Session = Depends(get_session)):
    service = EquipmentService(session)
    updated = service.update(equipment_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return updated


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, session: Session = Depends(get_session)):
    service = EquipmentService(session)
    deleted = service.delete(equipment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return None
