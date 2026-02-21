from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Notification, Driver, Vehicle
from schemas.schemas import NotificationCreate, NotificationResponse
from utils.security import get_current_driver
from typing import List
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/send", response_model=NotificationResponse)
async def send_notification(notification: NotificationCreate, db: AsyncSession = Depends(get_db)):
    # Find vehicle to find driver
    query = select(Vehicle).filter(Vehicle.plate_number == notification.plate_number.upper())
    result = await db.execute(query)
    vehicle = result.scalar()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    db_notification = Notification(
        driver_id=vehicle.driver_id,
        title=notification.title,
        message=notification.message,
        limit_type=notification.limit_type,
        timestamp=datetime.utcnow()
    )
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return db_notification

@router.get("/my", response_model=List[NotificationResponse])
async def get_notifications(db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(Notification).filter(Notification.driver_id == current_driver.driver_id).order_by(Notification.timestamp.desc())
    result = await db.execute(query)
    return result.scalars().all()
