from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import VirtualCard, Driver, Transaction, Notification
from utils.security import get_current_driver
from utils.crypto import decrypt_data

from datetime import datetime
from schemas.schemas import CardResponse, CardFreezeRequest, PayRequest, RedeemRequest, FastagPayRequest, OtpRequest, ResendDetailsRequest

router = APIRouter(prefix="/card", tags=["Card"])

# Ownership check now mostly redundant with get_current_driver using driver_id
def check_ownership(requested_plate_number: str, current_driver: Driver):
    # This might still be useful to verify if a plate belongs to the driver
    is_owner = any(v.plate_number == requested_plate_number.upper() for v in current_driver.vehicles)
    if not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized for this vehicle")

@router.post("/fastag/pay")
async def pay_fastag(req: FastagPayRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    # Verify the driver owns the vehicle
    check_ownership(req.plate_number, current_driver)
    
    # Verify Card
    query = select(VirtualCard).filter(VirtualCard.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    card = result.scalar()
    
    if not card or card.is_frozen:
        raise HTTPException(status_code=400, detail="Card is unavailable or frozen")
    if current_driver.wallet_points < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient Reward Balance")

    # Find the vehicle ID for logging
    v_query = select(Vehicle).filter(Vehicle.plate_number == req.plate_number.upper())
    v_res = await db.execute(v_query)
    vehicle = v_res.scalar()

    # Deduct Points
    current_driver.wallet_points -= req.amount
    
    # Log Transaction
    txn = Transaction(
        driver_id=current_driver.driver_id,
        transaction_type="Toll Payment",
        amount=-req.amount,
        balance_after=current_driver.wallet_points,
        description=f"Toll Pay: {req.toll_plaza_id} ({req.plate_number})",
        timestamp=datetime.utcnow()
    )
    db.add(txn)

    # Trigger Notification
    notif = Notification(
        driver_id=current_driver.driver_id,
        title="Toll Payment Successful 🛣️",
        message=f"₹ {req.amount} deducted for {req.plate_number} at {req.toll_plaza_id}.",
        limit_type="TOLL",
        timestamp=datetime.utcnow()
    )
    db.add(notif)

    await db.commit()
    
    return {"message": "Toll Payment Successful", "remaining_balance": current_driver.wallet_points}

@router.get("/my", response_model=CardResponse)
async def get_card(db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(VirtualCard).filter(VirtualCard.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    card = result.scalar()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Decrypt
    try:
        raw_card_num = decrypt_data(card.card_number)
        raw_cvv = decrypt_data(card.cvv) if hasattr(card, 'cvv') and card.cvv else "123"
    except:
        raw_card_num = "**** **** **** ****"
        raw_cvv = "***"

    return {
        "card_number": raw_card_num,
        "expiry_date": card.expiry_date,
        "cvv": raw_cvv,
        "card_balance": current_driver.wallet_points,
        "is_frozen": card.is_frozen,
        "owner_name": current_driver.owner_name
    }

@router.post("/send-otp")
async def send_otp(req: OtpRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    check_ownership(req.plate_number, current_driver)
    # Stub logic for demo: In real app, generate and send OTP
    return {"success": True, "message": "OTP sent to your registered email"}

@router.post("/resend-details")
async def resend_card_details(req: ResendDetailsRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    check_ownership(req.plate_number, current_driver)
    # Stub logic for demo
    if req.otp == "123456":
         return {"success": True, "message": "Card details have been resent to your email"}
    else:
         return {"success": False, "message": "Invalid OTP. Please try again."}

@router.post("/freeze")
async def freeze_card(req: CardFreezeRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(VirtualCard).filter(VirtualCard.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    card = result.scalar()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card.is_frozen = req.freeze
    await db.commit()
    return {"message": f"Card {'frozen' if req.freeze else 'unfrozen'} successfully"}

@router.post("/pay")
async def pay(req: PayRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(VirtualCard).filter(VirtualCard.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    card = result.scalar()
    
    if not card or card.is_frozen:
        raise HTTPException(status_code=400, detail="Card is unavailable or frozen")
    
    if current_driver.wallet_points < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Deduct Points
    current_driver.wallet_points -= req.amount
    
    # Log Transaction
    txn = Transaction(
        driver_id=current_driver.driver_id,
        transaction_type="PAYMENT",
        amount=-req.amount,
        balance_after=current_driver.wallet_points,
        description=f"Payment to {req.merchant}",
        timestamp=datetime.utcnow()
    )
    db.add(txn)
    await db.commit()
    
    return {"message": "Payment successful", "remaining_balance": current_driver.wallet_points}

@router.post("/redeem")
async def redeem(req: RedeemRequest, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    if current_driver.wallet_points < req.points:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    current_driver.wallet_points -= req.points
    
    txn = Transaction(
        driver_id=current_driver.driver_id,
        transaction_type="REDEEM",
        amount=-req.points,
        balance_after=current_driver.wallet_points,
        description=f"Redeemed for {req.redeem_type}",
        timestamp=datetime.utcnow()
    )
    db.add(txn)
    await db.commit()
    
    return {"message": "Redemption successful", "remaining_balance": current_driver.wallet_points}
