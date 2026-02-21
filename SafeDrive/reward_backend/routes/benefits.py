from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Driver
from pydantic import BaseModel

router = APIRouter(prefix="/driver", tags=["Driver Benefits"])

class BenefitsResponse(BaseModel):
    tier: str
    total_credits: int
    next_tier_progress: float
    next_tier_target: int
    parking_quota: int
    fuel_cashback: int
    service_coupon_count: int
    green_wave_eligible: bool

@router.get("/benefits/{plate_number}", response_model=BenefitsResponse)
async def get_driver_benefits(plate_number: str, db: AsyncSession = Depends(get_db)):
    query = select(Driver).filter(Driver.plate_number == plate_number.upper())
    result = await db.execute(query)
    driver = result.scalar()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    # Calculate Progress
    target = 500
    if driver.tier == "Bronze": target = 1000
    elif driver.tier == "Silver": target = 2000
    elif driver.tier == "Gold": target = 4000
    elif driver.tier == "Platinum": target = 4000 
    
    progress = 0.0
    if driver.tier != "Platinum":
        progress = min(1.0, driver.total_earned_credits / target)
    else:
        progress = 1.0

    return BenefitsResponse(
        tier=driver.tier,
        total_credits=driver.total_earned_credits,
        next_tier_progress=progress,
        next_tier_target=target,
        parking_quota=driver.parking_quota,
        fuel_cashback=driver.fuel_cashback,
        service_coupon_count=driver.service_coupon_count,
        green_wave_eligible=driver.tier in ["Gold", "Platinum"]
    )
