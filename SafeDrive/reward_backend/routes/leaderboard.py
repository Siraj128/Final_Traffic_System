from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Leaderboard, Driver, Vehicle
from schemas.schemas import LeaderboardEntry
from typing import List
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/top", response_model=List[LeaderboardEntry])
async def get_top_leaderboard(offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(Leaderboard)\
        .options(selectinload(Leaderboard.driver).selectinload(Driver.vehicles))\
        .order_by(Leaderboard.rank_position.asc())\
        .offset(offset)\
        .limit(limit)
    
    result = await db.execute(query)
    lb_entries = result.scalars().all()
    
    response = []
    for lb in lb_entries:
        driver = lb.driver
        primary_v = next((v for v in driver.vehicles if v.is_primary), None)
        if not primary_v and driver.vehicles:
            primary_v = driver.vehicles[0]
            
        response.append(LeaderboardEntry(
            plate_number=primary_v.plate_number if primary_v else "N/A",
            owner_name=driver.owner_name,
            wallet_points=driver.wallet_points,
            compliance_score=primary_v.compliance_score if primary_v else 100.0,
            rank_score=lb.rank_score,
            rank_position=lb.rank_position,
            avatar=driver.avatar
        ))
        
    return response

@router.get("/driver/{driver_id}", response_model=LeaderboardEntry)
async def get_user_rank(driver_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Leaderboard)\
        .options(selectinload(Leaderboard.driver).selectinload(Driver.vehicles))\
        .filter(Leaderboard.driver_id == driver_id)
    
    result = await db.execute(query)
    lb = result.scalar()
        
    if not lb:
        raise HTTPException(status_code=404, detail="Rank not found")
        
    driver = lb.driver
    primary_v = next((v for v in driver.vehicles if v.is_primary), None)
    if not primary_v and driver.vehicles:
        primary_v = driver.vehicles[0]

    return LeaderboardEntry(
        plate_number=primary_v.plate_number if primary_v else "N/A",
        owner_name=driver.owner_name,
        wallet_points=driver.wallet_points,
        compliance_score=primary_v.compliance_score if primary_v else 100.0,
        rank_score=lb.rank_score,
        rank_position=lb.rank_position,
        avatar=driver.avatar
    )

