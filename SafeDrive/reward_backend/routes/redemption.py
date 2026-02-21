from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from models.models import Driver, RedemptionCatalog, RedemptionTransaction, Transaction, Notification
from schemas.schemas import RewardItem, RedeemRequest, RedemptionResponse
from utils.security import get_current_driver
from typing import List
from datetime import datetime
import uuid

router = APIRouter(prefix="/rewards", tags=["Redemption Marketplace"])

@router.get("/catalog", response_model=List[RewardItem])
async def get_catalog(db: AsyncSession = Depends(get_db)):
    # Simple seeding if empty
    count_query = select(func.count(RedemptionCatalog.reward_id))
    count_res = await db.execute(count_query)
    if count_res.scalar() == 0:
        seed_data = [
            RedemptionCatalog(title="₹500 Fuel Voucher", description="Valid at Indian Oil & Shell", points_required=500, category="FUEL", vendor_name="Indian Oil"),
            RedemptionCatalog(title="Free Car Wash", description="Premium foam wash at GoMechanic", points_required=300, category="SERVICE", vendor_name="GoMechanic"),
            RedemptionCatalog(title="₹100 FASTag Top-up", description="Instant recharge for any FASTag", points_required=100, category="TOLL", vendor_name="Paytm"),
            RedemptionCatalog(title="Movie Ticket 50% Off", description="Valid on BookMyShow", points_required=200, category="SHOPPING", vendor_name="BookMyShow"),
            RedemptionCatalog(title="Parking Credit ₹50", description="Valid at City Centre Mall", points_required=50, category="PARKING", vendor_name="SmartPark"),
            RedemptionCatalog(title="10% Insurance Discount", description="On renewal with Acko", points_required=1000, category="INSURANCE", vendor_name="Acko"),
        ]
        db.add_all(seed_data)
        await db.commit()
        
    query = select(RedemptionCatalog).filter(RedemptionCatalog.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/redeem", response_model=RedemptionResponse)
async def redeem_reward(req: RedeemRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    # No longer need plate_number check if deductions are from unified wallet
        
    # 2. Verify Reward
    query = select(RedemptionCatalog).filter(RedemptionCatalog.reward_id == req.reward_id)
    result = await db.execute(query)
    reward = result.scalar()
    
    if not reward or not reward.is_active:
        raise HTTPException(status_code=404, detail="Reward not found or inactive")
        
    # 3. Check Balance
    if current_driver.wallet_points < reward.points_required:
        raise HTTPException(status_code=400, detail="Insufficient points")
        
    # 4. Process Redemption
    current_driver.wallet_points -= reward.points_required
    coupon_code = f"{reward.category[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
    
    # 5. Log Redemption Transaction
    redemption_txn = RedemptionTransaction(
        driver_id=current_driver.driver_id,
        reward_id=req.reward_id,
        points_spent=reward.points_required,
        status="SUCCESS",
        coupon_code=coupon_code,
        timestamp=datetime.utcnow()
    )
    db.add(redemption_txn)
    
    # 6. Log Wallet Transaction
    wallet_txn = Transaction(
        driver_id=current_driver.driver_id,
        transaction_type="REDEEM",
        amount=-reward.points_required,
        balance_after=current_driver.wallet_points,
        description=f"Redeemed: {reward.title}",
        timestamp=datetime.utcnow()
    )
    db.add(wallet_txn)
    
    # 7. Notification
    notif = Notification(
        driver_id=current_driver.driver_id,
        title="Redemption Successful 🎁",
        message=f"Used {reward.points_required} pts for {reward.title}. Code: {coupon_code}",
        limit_type="SYSTEM",
        timestamp=datetime.utcnow()
    )
    db.add(notif)
    
    await db.commit()
    
    return RedemptionResponse(
        success=True,
        message="Redemption Successful",
        coupon_code=coupon_code,
        remaining_balance=current_driver.wallet_points
    )

@router.get("/history")
async def get_redemption_history(db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(RedemptionTransaction, RedemptionCatalog)\
        .join(RedemptionCatalog, RedemptionTransaction.reward_id == RedemptionCatalog.reward_id)\
        .filter(RedemptionTransaction.driver_id == current_driver.driver_id)\
        .order_by(RedemptionTransaction.timestamp.desc())
        
    result = await db.execute(query)
    rows = result.all()
        
    history = []
    for txn, reward in rows:
        history.append({
            "transaction_id": txn.transaction_id,
            "reward_title": reward.title,
            "points_spent": txn.points_spent,
            "coupon_code": txn.coupon_code,
            "timestamp": txn.timestamp,
            "status": txn.status
        })
    return history
