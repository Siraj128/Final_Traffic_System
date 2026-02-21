from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Driver
from schemas.schemas import DriverResponse, UserUpdate
from utils.security import get_current_driver

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/{plate_number}", response_model=DriverResponse)
async def get_user_profile(plate_number: str, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    if plate_number.upper() != current_driver.plate_number.upper():
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")
        
    return current_driver

@router.put("/{plate_number}", response_model=DriverResponse)
async def update_user_profile(plate_number: str, update_data: UserUpdate, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    if plate_number.upper() != current_driver.plate_number.upper():
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    if update_data.name:
        current_driver.owner_name = update_data.name
    if update_data.avatar:
        current_driver.avatar = update_data.avatar
        
    await db.commit()
    await db.refresh(current_driver)
    return current_driver
