from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from models.models import Driver, DriverAnalytics, Reward, Violation, RedemptionTransaction, SystemConfig, RedemptionCatalog
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from routes.events import verify_internal_token

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"], dependencies=[Depends(verify_internal_token)])

# --- Schemas ---
class AdminStats(BaseModel):
    total_drivers: int
    active_drivers: int
    total_rewards_issued: int
    total_violations: int
    pending_redemptions: int

class TierDistribution(BaseModel):
    bronze: int
    silver: int
    gold: int
    platinum: int

class RiskDistribution(BaseModel):
    safe: int
    moderate: int
    high_risk: int

class AdminDashboardResponse(BaseModel):
    stats: AdminStats
    tiers: TierDistribution
    risks: RiskDistribution

class ConfigUpdate(BaseModel):
    fuel_cashback_rate: float
    parking_quota_base: int
    green_wave_min_tier: str
    violation_penalty_multiplier: float

# --- Endpoints ---

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # 1. Driver Stats
    total_drivers = (await db.execute(select(func.count(Driver.driver_id)))).scalar() or 0
    active_drivers = total_drivers 

    # 2. Rewards & Violations
    total_rewards = (await db.execute(select(func.count(Reward.reward_id)))).scalar() or 0
    total_violations = (await db.execute(select(func.count(Violation.violation_id)))).scalar() or 0

    # 3. Pending Redemptions
    p_query = select(func.count(RedemptionTransaction.transaction_id)).filter(RedemptionTransaction.status == "PENDING")
    pending_redemptions = (await db.execute(p_query)).scalar() or 0

    # 4. Tier Dist
    t_query = select(Driver.tier, func.count(Driver.tier)).group_by(Driver.tier)
    tiers = (await db.execute(t_query)).all()
    tier_dict = {t[0]: t[1] for t in tiers}
    
    # 5. Risk Dist
    r_query = select(DriverAnalytics.risk_level, func.count(DriverAnalytics.risk_level)).group_by(DriverAnalytics.risk_level)
    risks = (await db.execute(r_query)).all()
    risk_dict = {r[0]: r[1] for r in risks}

    return AdminDashboardResponse(
        stats=AdminStats(
            total_drivers=total_drivers,
            active_drivers=active_drivers,
            total_rewards_issued=total_rewards,
            total_violations=total_violations,
            pending_redemptions=pending_redemptions
        ),
        tiers=TierDistribution(
            bronze=tier_dict.get("Bronze", 0),
            silver=tier_dict.get("Silver", 0),
            gold=tier_dict.get("Gold", 0),
            platinum=tier_dict.get("Platinum", 0)
        ),
        risks=RiskDistribution(
            safe=risk_dict.get("SAFE", 0),
            moderate=risk_dict.get("MODERATE", 0),
            high_risk=risk_dict.get("RISK", 0)
        )
    )

@router.get("/config")
async def get_config(db: AsyncSession = Depends(get_db)):
    query = select(SystemConfig)
    result = await db.execute(query)
    config = result.scalar()
    if not config:
        config = SystemConfig()
        db.add(config)
        await db.commit()
    return config

@router.post("/config")
async def update_config(update: ConfigUpdate, db: AsyncSession = Depends(get_db)):
    query = select(SystemConfig)
    result = await db.execute(query)
    config = result.scalar()
    if not config:
        config = SystemConfig()
        db.add(config)
    
    config.fuel_cashback_rate = update.fuel_cashback_rate
    config.parking_quota_base = update.parking_quota_base
    config.green_wave_min_tier = update.green_wave_min_tier
    config.violation_penalty_multiplier = update.violation_penalty_multiplier
    config.last_updated = datetime.utcnow()
    
    await db.commit()
    return {"message": "Configuration updated"}

@router.get("/redemptions")
async def get_redemptions(status: str = "ALL", db: AsyncSession = Depends(get_db)):
    query = select(RedemptionTransaction, RedemptionCatalog).join(RedemptionCatalog)
    if status != "ALL":
        query = query.filter(RedemptionTransaction.status == status)
    
    result = await db.execute(query.order_by(RedemptionTransaction.timestamp.desc()))
    # Simple formatting for response if needed, but returning full objects for now
    return result.scalars().all()

@router.post("/redemptions/{txn_id}/{action}")
async def process_redemption(txn_id: int, action: str, db: AsyncSession = Depends(get_db)):
    query = select(RedemptionTransaction).filter(RedemptionTransaction.transaction_id == txn_id)
    result = await db.execute(query)
    txn = result.scalar()
    
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if action.upper() == "APPROVE":
        txn.status = "APPROVED"
    elif action.upper() == "REJECT":
        txn.status = "REJECTED"
        q_driver = select(Driver).filter(Driver.plate_number == txn.plate_number)
        res_driver = await db.execute(q_driver)
        driver = res_driver.scalar()
        if driver:
            driver.wallet_points += txn.points_spent
            
    await db.commit()
    return {"message": f"Redemption {action}D"}
