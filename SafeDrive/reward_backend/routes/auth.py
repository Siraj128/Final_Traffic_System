from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import Driver, VirtualCard, Vehicle, DriverAnalytics
from schemas.schemas import DriverCreate, DriverResponse, LoginRequest, Token
from utils.security import get_password_hash, verify_password, create_access_token, get_current_driver
from utils.crypto import encrypt_data, generate_luhn_card_number
from utils.config import Config
from sqlalchemy.orm import selectinload
import random

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me")
async def get_me(current_driver: Driver = Depends(get_current_driver)):
    return current_driver

@router.post("/register", response_model=DriverResponse)
async def register(driver: DriverCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    query = select(Driver).filter(Driver.email == driver.email.lower())
    result = await db.execute(query)
    if result.scalar():
        raise HTTPException(status_code=400, detail="User with this email already registered")

    # Check if plate exists
    query = select(Vehicle).filter(Vehicle.plate_number == driver.plate_number.upper())
    result = await db.execute(query)
    if result.scalar():
        raise HTTPException(status_code=400, detail="Vehicle with this plate number already registered")

    # Create Driver
    hashed_password = get_password_hash(driver.password)
    new_driver = Driver(
        owner_name=driver.owner_name,
        email=driver.email.lower(),
        mobile=driver.mobile,
        password_hash=hashed_password,
        wallet_points=500,
        tier="Bronze"
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)

    # Create Initial Vehicle (Primary)
    new_vehicle = Vehicle(
        driver_id=new_driver.driver_id,
        plate_number=driver.plate_number.upper(),
        vehicle_type=driver.vehicle_type,
        is_primary=True,
        compliance_score=100.0
    )
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)

    # Initialize Analytics
    analytics = DriverAnalytics(vehicle_id=new_vehicle.vehicle_id)
    db.add(analytics)

    # Generate Secure Virtual Card
    raw_card_number = generate_luhn_card_number()
    raw_cvv = str(random.randint(100, 999))
    
    new_card = VirtualCard(
        driver_id=new_driver.driver_id,
        card_number=encrypt_data(raw_card_number),
        expiry_date="12/28",
        cvv=encrypt_data(raw_cvv),
        card_balance=new_driver.wallet_points
    )
    db.add(new_card)
    await db.commit()
    await db.refresh(new_driver)

    # Reload with vehicles
    query = select(Driver).filter(Driver.driver_id == new_driver.driver_id).options(selectinload(Driver.vehicles))
    result = await db.execute(query)
    return result.scalar()

@router.post("/login", response_model=Token)
async def login(login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find driver by email or plate
    driver = None
    if "@" in login_req.identifier:
        query = select(Driver).filter(Driver.email == login_req.identifier.lower()).options(selectinload(Driver.vehicles))
        result = await db.execute(query)
        driver = result.scalar()
    else:
        # Try finding by plate
        query = select(Driver).join(Vehicle).filter(Vehicle.plate_number == login_req.identifier.upper()).options(selectinload(Driver.vehicles))
        result = await db.execute(query)
        driver = result.scalar()
    
    if not driver:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect identifier or password")
    
    if not verify_password(login_req.password, driver.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect identifier or password")
    
    access_token = create_access_token(data={"sub": str(driver.driver_id)})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": driver
    }

@router.post("/google")
async def google_login(req: dict, db: AsyncSession = Depends(get_db)):
    token = req.get('idToken')
    if not token:
        raise HTTPException(status_code=404, detail="Missing Google ID Token")
        
    try:
        # In production, verify properly
        if not token.startswith("ey"):
             raise ValueError("Invalid Token Format")
             
        email = req.get('email')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google Token: {str(e)}")
    
    if email:
        query = select(Driver).filter(Driver.email == email).options(selectinload(Driver.vehicles))
        result = await db.execute(query)
        driver = result.scalar()
        
        if driver:
             access_token = create_access_token(data={"sub": str(driver.driver_id)})
             return {
                 "token": access_token,
                 "token_type": "bearer",
                 "user": driver,
                 "isNewUser": False
             }

    return {
        "isNewUser": True,
        "googleId": req.get('googleId'),
        "name": req.get('name'),
        "email": req.get('email'),
        "picture": req.get('picture')
    }

@router.post("/google/register")
async def google_register(data: dict, db: AsyncSession = Depends(get_db)):
    plate = data.get('vehicle_number', '').upper()
    if not plate:
        raise HTTPException(status_code=400, detail="Vehicle number is required")
        
    query = select(Vehicle).filter(Vehicle.plate_number == plate)
    result = await db.execute(query)
    if result.scalar():
        raise HTTPException(status_code=400, detail="Vehicle already registered")

    # Create Driver
    new_driver = Driver(
        owner_name=data.get('name'),
        email=data.get('email'),
        mobile=data.get('mobile', ''),
        password_hash="google_auth", 
        wallet_points=500,
        avatar=data.get('avatar'),
        tier="Bronze"
    )
    db.add(new_driver)
    await db.commit()
    await db.refresh(new_driver)

    # Create Vehicle
    new_vehicle = Vehicle(
        driver_id=new_driver.driver_id,
        plate_number=plate,
        vehicle_type=data.get('vehicle_type', 'Car'),
        is_primary=True,
        compliance_score=100.0
    )
    db.add(new_vehicle)
    
    # Initialize Analytics
    analytics = DriverAnalytics(vehicle_id=new_vehicle.vehicle_id)
    db.add(analytics)

    # Generate Secure Card
    raw_card_number = generate_luhn_card_number()
    raw_cvv = str(random.randint(100, 999))
    
    new_card = VirtualCard(
        driver_id=new_driver.driver_id,
        card_number=encrypt_data(raw_card_number),
        expiry_date="12/28",
        cvv=encrypt_data(raw_cvv),
        card_balance=new_driver.wallet_points
    )
    db.add(new_card)
    await db.commit()
    await db.refresh(new_driver)

    # Reload with vehicles
    query = select(Driver).filter(Driver.driver_id == new_driver.driver_id).options(selectinload(Driver.vehicles))
    result = await db.execute(query)
    populated_driver = result.scalar()

    access_token = create_access_token(data={"sub": str(new_driver.driver_id)})
    return {
        "success": True,
        "token": access_token,
        "user": populated_driver
    }
