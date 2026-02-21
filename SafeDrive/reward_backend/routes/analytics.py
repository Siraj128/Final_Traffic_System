from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from models.models import Driver, DriverAnalytics, Reward, Violation, Vehicle
from schemas.schemas import AnalyticsResponse
from datetime import datetime, timedelta
from typing import List
from utils.security import get_current_driver
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/analytics", tags=["AI Driving Analytics"])

async def calculate_driving_score(vehicle: Vehicle, db: AsyncSession) -> float:
    # 1. Compliance Score (Base on Vehicle)
    compliance = vehicle.compliance_score
    
    # 2. Reward Factor (Vehicle specific)
    query_rewards = select(func.sum(Reward.reward_points)).filter(Reward.vehicle_id == vehicle.vehicle_id)
    res_rewards = await db.execute(query_rewards)
    total_rewards = res_rewards.scalar() or 0
    reward_factor = min(100.0, (total_rewards / 1000.0) * 100)
    
    # 3. Violation Factor 
    last_30_days = datetime.utcnow() - timedelta(days=30)
    query_v = select(func.count(Violation.violation_id)).filter(
        Violation.vehicle_id == vehicle.vehicle_id,
        Violation.timestamp >= last_30_days
    )
    result_v = await db.execute(query_v)
    violation_count = result_v.scalar() or 0
    
    violation_penalty = min(100.0, violation_count * 20.0)
    
    # Weighted Formula
    score = (compliance * 0.5) + (reward_factor * 0.3) - (violation_penalty * 0.2)
    
    return max(0.0, min(100.0, score))

def get_risk_level(score: float) -> str:
    if score >= 85: return "SAFE"
    elif score >= 60: return "MODERATE"
    else: return "RISK"

async def generate_insights(vehicle: Vehicle, score: float, db: AsyncSession) -> List[str]:
    insights = []
    
    if score >= 85:
        insights.append(f"Outstanding! {vehicle.plate_number} follows elite safety standards.")
    elif score >= 70:
        insights.append("Good consistency. Aim for zero signal violations to reach SAFE status.")
    else:
        insights.append("Critical: Frequent violations detected. Road safety training recommended.")
        
    if vehicle.compliance_score < 80:
        v_query = select(Violation.violation_type).filter(Violation.vehicle_id == vehicle.vehicle_id).limit(1)
        v_res = await db.execute(v_query)
        v_type = v_res.scalar()
        if v_type:
            insights.append(f"Frequent {v_type} detected. This is lowering your score.")
        else:
            insights.append("Low vehicle compliance. Maintain lane discipline.")
            
    return insights

@router.get("/vehicle/{vehicle_id}", response_model=AnalyticsResponse)
async def get_analytics(vehicle_id: int, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id, Vehicle.driver_id == current_driver.driver_id).options(selectinload(Vehicle.rewards), selectinload(Vehicle.violations))
    result = await db.execute(query)
    vehicle = result.scalar()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or unauthorized")
        
    # Check if analytics entry exists
    query_an = select(DriverAnalytics).filter(DriverAnalytics.vehicle_id == vehicle_id)
    result_an = await db.execute(query_an)
    analytics = result_an.scalar()
    
    # Recalculate
    score = await calculate_driving_score(vehicle, db)
    risk = get_risk_level(score)
    insights = await generate_insights(vehicle, score, db)
    
    if not analytics:
        analytics = DriverAnalytics(vehicle_id=vehicle_id)
        db.add(analytics)
    
    analytics.driving_score = score
    analytics.risk_level = risk
    analytics.last_updated = datetime.utcnow()
    analytics.total_rewards = len(vehicle.rewards)
    analytics.total_violations = len(vehicle.violations)
    
    await db.commit()
    
    return AnalyticsResponse(
        plate_number=vehicle.plate_number,
        driving_score=score,
        risk_level=risk,
        safe_streak_days=analytics.safe_streak_days,
        total_rewards=analytics.total_rewards,
        total_violations=analytics.total_violations,
        insights=insights
    )
