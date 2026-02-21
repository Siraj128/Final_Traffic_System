from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.models import TrafficRule
from schemas.schemas import TrafficRuleSchema
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    fine: Optional[str] = None
    impact: Optional[str] = None

@router.post("/query", response_model=ChatResponse)
async def query_assistant(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    lower_msg = request.message.lower()
    
    # 1. Fetch All Rules (Caching would be better, but for hackathon this works)
    query = select(TrafficRule)
    result = await db.execute(query)
    rules = result.scalars().all()
    
    # Simple Keyword Matcher
    for rule in rules:
        keywords = [k.strip().lower() for k in rule.keywords.split(",")]
        if any(k in lower_msg for k in keywords):
            return ChatResponse(
                reply=rule.answer,
                fine=rule.fine_amount,
                impact=rule.impact
            )
            
    # 2. Fallback Logic
    return ChatResponse(
        reply="I couldn't find a specific rule for that in my database. Generally, following traffic signals and lane discipline is mandatory. Please check official RTO guidelines.",
        fine="Varies",
        impact="Negative"
    )

@router.get("/rules", response_model=List[TrafficRuleSchema])
async def get_all_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrafficRule))
    return result.scalars().all()

@router.post("/seed")
async def seed_rules(db: AsyncSession = Depends(get_db)):
    # Seed common rules if empty
    check = await db.execute(select(TrafficRule))
    if check.first():
        return {"message": "Rules already seeded"}
        
    rules = [
        TrafficRule(category="FINES", keywords="signal,red light,jump", question="Signal Jump", answer="Jumping a red light is a serious violation. Under the MV Act, you may be fined ₹1,000.", fine_amount="₹1,000", impact="-5 Score"),
        TrafficRule(category="FINES", keywords="helmet,safety,headgear", question="Helmet Violation", answer="Wearing a helmet is mandatory for the rider and pillion. The fine is ₹500.", fine_amount="₹500", impact="-2 Score"),
        TrafficRule(category="FINES", keywords="alcohol,drunk,drinking", question="Drunk Driving", answer="Drunk driving is a criminal offense with fines up to ₹10,000.", fine_amount="₹10,000", impact="Critical"),
        TrafficRule(category="FINES", keywords="seatbelt,belt", question="Seatbelt Violation", answer="Not wearing a seatbelt attracts a fine of ₹1,000.", fine_amount="₹1,000", impact="-3 Score"),
        TrafficRule(category="RULES", keywords="parking,wrong side", question="Wrong Parking", answer="Parking in a no-parking zone can lead to towing and a ₹500 fine.", fine_amount="₹500", impact="-1 Score"),
    ]
    db.add_all(rules)
    await db.commit()
    return {"message": "Rules seeded successfully"}
