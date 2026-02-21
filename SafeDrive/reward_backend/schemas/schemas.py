from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user: DriverResponse

class TokenData(BaseModel):
    driver_id: Optional[int] = None

# Driver
class VehicleResponse(BaseModel):
    vehicle_id: int
    plate_number: str
    vehicle_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    fastag_id: Optional[str] = None
    is_primary: bool
    compliance_score: float
    safe_streak_days: int

    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    plate_number: str
    vehicle_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    fastag_id: Optional[str] = None

class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    fastag_id: Optional[str] = None
    vehicle_type: Optional[str] = None

class DriverCreate(BaseModel):
    owner_name: str
    email: str
    mobile: str
    password: str
    # First vehicle info
    plate_number: str
    vehicle_type: str

class DriverResponse(BaseModel):
    driver_id: int
    owner_name: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    wallet_points: int
    tier: str
    total_earned_credits: int
    parking_quota: int
    fuel_cashback: int
    service_coupon_count: int
    avatar: Optional[str] = None
    vehicles: List[VehicleResponse] = []

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    identifier: str # email or plate
    password: str

class GoogleLoginRequest(BaseModel):
    idToken: str

# Wallet
class WalletResponse(BaseModel):
    plate_number: str
    wallet_points: int
    compliance_score: float

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None

# Card
class CardResponse(BaseModel):
    card_number: str # Will be masked (**** **** **** 1234)
    expiry_date: str
    cvv: str # Masked (***)
    card_balance: int
    is_frozen: bool
    owner_name: str

class CardFreezeRequest(BaseModel):
    plate_number: str
    freeze: bool

class PayRequest(BaseModel):
    plate_number: str
    amount: int
    merchant: str

class OtpRequest(BaseModel):
    plate_number: str

class ResendDetailsRequest(BaseModel):
    plate_number: str
    otp: str

class FastagPayRequest(BaseModel):
    plate_number: str
    amount: int
    toll_plaza_id: str

class RedeemRequest(BaseModel):
    plate_number: str
    redeem_type: str # FUEL, TOLL
    points: int

# Events
class RewardEvent(BaseModel):
    plate_number: str
    points: int
    reason: str
    junction_id: Optional[str] = None

class ViolationEvent(BaseModel):
    plate_number: str
    penalty_points: int
    violation_type: str
    junction_id: Optional[str] = None

# Transactions
class TransactionResponse(BaseModel):
    transaction_id: int
    type: str
    amount: int
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Notifications
class NotificationCreate(BaseModel):
    plate_number: str
    title: str
    message: str
    limit_type: str

class NotificationResponse(BaseModel):
    notification_id: int
    title: str
    message: str
    limit_type: str
    is_read: bool
    timestamp: datetime

    class Config:
        from_attributes = True

# Leaderboard
class LeaderboardEntry(BaseModel):
    plate_number: str
    owner_name: str
    wallet_points: int
    compliance_score: float
    rank_score: float
    rank_position: int
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

# Redemption
class RewardItem(BaseModel):
    reward_id: int
    title: str
    description: str
    points_required: int
    category: str
    vendor_name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class RedeemRequest(BaseModel):
    plate_number: str
    reward_id: int

class RedemptionResponse(BaseModel):
    success: bool
    message: str
    coupon_code: Optional[str] = None
    remaining_balance: int

# Analytics
class AnalyticsResponse(BaseModel):
    plate_number: str
    driving_score: float
    risk_level: str
    safe_streak_days: int
    total_rewards: int
    total_violations: int
    insights: List[str] = []


# Traffic Assistant
class TrafficRuleSchema(BaseModel):
    rule_id: int
    category: str
    keywords: str
    question: str
    answer: str
    fine_amount: Optional[str] = None
    impact: Optional[str] = None

    class Config:
        from_attributes = True
