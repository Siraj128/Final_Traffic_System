from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.connection import get_db
from models.models import Vehicle, Driver, DriverAnalytics
from schemas.schemas import VehicleCreate, VehicleResponse, VehicleUpdate
from utils.security import get_current_driver

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.post("/add", response_model=VehicleResponse)
async def add_vehicle(vehicle_data: VehicleCreate, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    # Check if plate already registered
    query = select(Vehicle).filter(Vehicle.plate_number == vehicle_data.plate_number.upper())
    result = await db.execute(query)
    if result.scalar():
        raise HTTPException(status_code=400, detail="Vehicle with this plate number already registered")

    # If first vehicle, make it primary
    is_primary = len(current_driver.vehicles) == 0

    new_vehicle = Vehicle(
        driver_id=current_driver.driver_id,
        plate_number=vehicle_data.plate_number.upper(),
        vehicle_type=vehicle_data.vehicle_type,
        brand=vehicle_data.brand,
        model=vehicle_data.model,
        color=vehicle_data.color,
        fastag_id=vehicle_data.fastag_id,
        is_primary=is_primary
    )
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)

    # Initialize Analytics for this vehicle
    analytics = DriverAnalytics(vehicle_id=new_vehicle.vehicle_id)
    db.add(analytics)
    await db.commit()

    return new_vehicle

@router.get("/user/{user_id}", response_model=list[VehicleResponse])
async def get_user_vehicles(user_id: int, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    if current_driver.driver_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view your own vehicles")
    
    query = select(Vehicle).filter(Vehicle.driver_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my", response_model=list[VehicleResponse])
async def get_my_vehicles(current_driver: Driver = Depends(get_current_driver)):
    return current_driver.vehicles

@router.put("/update/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: int, vehicle_update: VehicleUpdate, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id, Vehicle.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    vehicle = result.scalar()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or unauthorized")

    update_data = vehicle_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vehicle, key, value)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle

@router.delete("/delete/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    query = select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id, Vehicle.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    vehicle = result.scalar()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or unauthorized")

    if vehicle.is_primary:
        # Check if there are other vehicles to promote
        query_others = select(Vehicle).filter(Vehicle.driver_id == current_driver.driver_id, Vehicle.vehicle_id != vehicle_id)
        others_result = await db.execute(query_others)
        next_v = others_result.scalars().first()
        if next_v:
            next_v.is_primary = True

    await db.delete(vehicle)
    await db.commit()
    return {"success": True, "message": "Vehicle deleted"}

@router.patch("/set-primary/{vehicle_id}", response_model=VehicleResponse)
async def set_primary_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db), current_driver: Driver = Depends(get_current_driver)):
    # Verify ownership
    query = select(Vehicle).filter(Vehicle.vehicle_id == vehicle_id, Vehicle.driver_id == current_driver.driver_id)
    result = await db.execute(query)
    target_vehicle = result.scalar()
    
    if not target_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or unauthorized")

    # Reset others
    await db.execute(
        update(Vehicle)
        .where(Vehicle.driver_id == current_driver.driver_id)
        .values(is_primary=False)
    )
    
    target_vehicle.is_primary = True
    await db.commit()
    await db.refresh(target_vehicle)
    return target_vehicle
