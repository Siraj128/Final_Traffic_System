from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Driver, Transaction, Reward, Violation, Notification, Vehicle
from datetime import datetime
from schemas.schemas import RewardEvent, ViolationEvent
from utils.config import Config
from utils.ranking import update_driver_rank
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/events", tags=["Events"])

def verify_internal_token(x_internal_token: str = Header(...)):
    if x_internal_token != Config.INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Internal Token")

@router.post("/reward")
async def add_reward(event: RewardEvent, db: AsyncSession = Depends(get_db), authenticated: bool = Depends(verify_internal_token)):
    # Find vehicle first
    query = select(Vehicle).options(joinedload(Vehicle.owner)).filter(Vehicle.plate_number == event.plate_number.upper())
    result = await db.execute(query)
    vehicle = result.scalar()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    driver = vehicle.owner
    
    # Credit unified wallet
    driver.wallet_points += event.points
    driver.total_earned_credits += event.points 
    
    # Update vehicle-specific compliance score
    vehicle.compliance_score = min(100.0, vehicle.compliance_score + 0.5)
    
    # Tier progression (Unified)
    new_tier = driver.tier
    if driver.total_earned_credits >= 4000: new_tier = "Platinum"
    elif driver.total_earned_credits >= 2000: new_tier = "Gold"
    elif driver.total_earned_credits >= 1000: new_tier = "Silver"
    elif driver.total_earned_credits >= 500: new_tier = "Bronze"

    if new_tier != driver.tier:
        driver.tier = new_tier
        if new_tier == "Silver": 
            driver.parking_quota = 5
            driver.service_coupon_count += 1
        elif new_tier == "Gold": 
            driver.parking_quota = 10
            driver.service_coupon_count += 2
        elif new_tier == "Platinum": 
            driver.parking_quota = 20
            driver.service_coupon_count += 3
            
        notif_up = Notification(
            driver_id=driver.driver_id,
            title=f"Level Up! {new_tier} Tier 🌟",
            message=f"Welcome to {new_tier}! Enjoy exclusive benefits.",
            limit_type="SYSTEM",
            timestamp=datetime.utcnow()
        )
        db.add(notif_up)
    
    reward = Reward(
        driver_id=driver.driver_id,
        vehicle_id=vehicle.vehicle_id,
        reward_type=event.reason,
        reward_points=event.points,
        junction_id=event.junction_id
    )
    db.add(reward)
    
    txn = Transaction(
        driver_id=driver.driver_id,
        transaction_type="REWARD",
        amount=event.points,
        balance_after=driver.wallet_points,
        description=f"Reward ({vehicle.plate_number}): {event.reason}",
        timestamp=datetime.utcnow()
    )
    db.add(txn)

    notif = Notification(
        driver_id=driver.driver_id,
        title="Reward Earned 🎉",
        message=f"+{event.points} points credited for {event.reason} ({vehicle.plate_number}).",
        limit_type="REWARD",
        timestamp=datetime.utcnow()
    )
    db.add(notif)
    
    await db.commit()
    # update_driver_rank might need update too if it relies on plate
    await update_driver_rank(db, driver.driver_id)
    
    return {"message": "Reward credited", "new_balance": driver.wallet_points}

@router.post("/violation")
async def add_violation(event: ViolationEvent, db: AsyncSession = Depends(get_db), authenticated: bool = Depends(verify_internal_token)):
    # Find vehicle first
    query = select(Vehicle).options(joinedload(Vehicle.owner)).filter(Vehicle.plate_number == event.plate_number.upper())
    result = await db.execute(query)
    vehicle = result.scalar()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    driver = vehicle.owner
    
    # Deduct from unified wallet
    driver.wallet_points -= event.penalty_points
    
    # Update vehicle-specific compliance score
    vehicle.compliance_score = max(0.0, vehicle.compliance_score - 2.0)
    
    violation = Violation(
        driver_id=driver.driver_id,
        vehicle_id=vehicle.vehicle_id,
        violation_type=event.violation_type,
        penalty_points=event.penalty_points,
        junction_id=event.junction_id
    )
    db.add(violation)
    
    txn = Transaction(
        driver_id=driver.driver_id,
        transaction_type="VIOLATION",
        amount=-event.penalty_points,
        balance_after=driver.wallet_points,
        description=f"Violation ({vehicle.plate_number}): {event.violation_type}",
        timestamp=datetime.utcnow()
    )
    db.add(txn)

    notif = Notification(
        driver_id=driver.driver_id,
        title="Violation Detected ⚠️",
        message=f"-{event.penalty_points} points deducted for {event.violation_type} on {vehicle.plate_number}.",
        limit_type="VIOLATION",
        timestamp=datetime.utcnow()
    )
    db.add(notif)

    await db.commit()
    return {"message": "Violation logged", "new_balance": driver.wallet_points}
