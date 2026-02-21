from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Driver, Transaction
from schemas.schemas import WalletResponse, TransactionResponse
from utils.security import get_current_driver
from typing import List

router = APIRouter(prefix="/wallet", tags=["Wallet"])

@router.get("/my", response_model=WalletResponse)
async def get_wallet(db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    # Find primary vehicle for compliance score
    primary_vehicle = next((v for v in current_driver.vehicles if v.is_primary), None)
    if not primary_vehicle and current_driver.vehicles:
        primary_vehicle = current_driver.vehicles[0]
    
    comp_score = primary_vehicle.compliance_score if primary_vehicle else 100.0
    plate = primary_vehicle.plate_number if primary_vehicle else "N/A"

    return {
        "plate_number": plate,
        "wallet_points": current_driver.wallet_points,
        "compliance_score": comp_score
    }

@router.get("/history", response_model=List[TransactionResponse])
async def get_history(db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(Transaction).filter(Transaction.driver_id == current_driver.driver_id).order_by(Transaction.timestamp.desc())
    result = await db.execute(query)
    transactions = result.scalars().all()
    return transactions
