from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String)
    mobile = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    wallet_points = Column(Integer, default=500)
    avatar = Column(String, nullable=True)
    
    # Tier System
    tier = Column(String, default="Bronze")
    total_earned_credits = Column(Integer, default=0)
    parking_quota = Column(Integer, default=0)
    fuel_cashback = Column(Integer, default=0)
    service_coupon_count = Column(Integer, default=0)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    virtual_card = relationship("VirtualCard", back_populates="driver", uselist=False)
    transactions = relationship("Transaction", back_populates="driver")
    rewards = relationship("Reward", back_populates="driver")
    violations = relationship("Violation", back_populates="driver")
    notifications = relationship("Notification", back_populates="driver")

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    plate_number = Column(String, unique=True, index=True)
    vehicle_type = Column(String) # Car, Bike, Truck, etc.
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    color = Column(String, nullable=True)
    fastag_id = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
    compliance_score = Column(Float, default=100.0)
    safe_streak_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Driver", back_populates="vehicles")
    rewards = relationship("Reward", back_populates="vehicle")
    violations = relationship("Violation", back_populates="vehicle")
    analytics = relationship("DriverAnalytics", back_populates="vehicle", uselist=False)

class VirtualCard(Base):
    __tablename__ = "virtual_cards"

    card_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    card_number = Column(String, unique=True)
    expiry_date = Column(String)
    cvv = Column(String)
    card_balance = Column(Integer, default=0)
    is_frozen = Column(Boolean, default=False)

    driver = relationship("Driver", back_populates="virtual_card")

class Reward(Base):
    __tablename__ = "rewards"

    reward_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"))
    reward_type = Column(String)
    reward_points = Column(Integer)
    junction_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="rewards")
    vehicle = relationship("Vehicle", back_populates="rewards")

class Violation(Base):
    __tablename__ = "violations"

    violation_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"))
    violation_type = Column(String)
    penalty_points = Column(Integer)
    junction_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="violations")
    vehicle = relationship("Vehicle", back_populates="violations")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    transaction_type = Column(String) # REWARD, VIOLATION, REDEEM, PAYMENT
    amount = Column(Integer)
    balance_after = Column(Integer)
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="transactions")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    title = Column(String)
    message = Column(String)
    limit_type = Column(String) # REWARD, VIOLATION, TOLL, SYSTEM
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="notifications")

class Leaderboard(Base):
    __tablename__ = "leaderboard"

    leaderboard_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"), unique=True)
    rank_score = Column(Float, default=0.0)
    rank_position = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver")

class RedemptionCatalog(Base):
    __tablename__ = "redemption_catalog"

    reward_id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    points_required = Column(Integer)
    category = Column(String) # FUEL, TOLL, SERVICE, SHOPPING
    vendor_name = Column(String)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class RedemptionTransaction(Base):
    __tablename__ = "redemption_transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.driver_id"))
    reward_id = Column(Integer, ForeignKey("redemption_catalog.reward_id"))
    points_spent = Column(Integer)
    status = Column(String, default="SUCCESS")
    coupon_code = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver")
    reward = relationship("RedemptionCatalog")

class DriverAnalytics(Base):
    __tablename__ = "driver_analytics"

    analytics_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), unique=True)
    driving_score = Column(Float, default=100.0)
    risk_level = Column(String, default="SAFE") # SAFE, MODERATE, RISK
    safe_streak_days = Column(Integer, default=0)
    total_rewards = Column(Integer, default=0)
    total_violations = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="analytics")

class SystemConfig(Base):
    __tablename__ = "system_config"

    config_id = Column(Integer, primary_key=True, index=True)
    fuel_cashback_rate = Column(Float, default=0.05) # 5%
    parking_quota_base = Column(Integer, default=2) # 2 hours
    green_wave_min_tier = Column(String, default="Gold")
    violation_penalty_multiplier = Column(Float, default=1.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class TrafficRule(Base):
    __tablename__ = "traffic_rules"

    rule_id = Column(Integer, primary_key=True, index=True)
    category = Column(String) # FINES, SAFETY, PARKING
    keywords = Column(String) # comma-separated
    question = Column(String)
    answer = Column(String)
    fine_amount = Column(String, nullable=True)
    impact = Column(String, nullable=True)
