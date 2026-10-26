from fastapi import APIRouter, Depends, status
from fastapi.param_functions import Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db

from app.domains.rooms.schemas import BuildingResponse, BuildingCreate
from app.domains.rooms.services import BuildingService
router = APIRouter(
    prefix="/buildings",
    tags=["buildings"],
)

@router.get("", response_model=list[BuildingResponse], status_code=status.HTTP_200_OK)
async def get_buildings(
    db: AsyncSession = Depends(get_db)
):
    service = BuildingService(db)
    return await service.get_all_buildings()

@router.post("", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    building_data: BuildingCreate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    service = BuildingService(db)
    return await service.create_building(building_data)