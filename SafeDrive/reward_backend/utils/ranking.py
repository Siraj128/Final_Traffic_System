from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Leaderboard, Driver
from services.email_service import send_rank_upgrade_email

def get_tier(credits):
    if credits >= 2000: return "Gold"
    if credits >= 1000: return "Silver"
    return "Bronze"

async def update_driver_rank(db: AsyncSession, driver_id: int):
    query = select(Driver).filter(Driver.driver_id == driver_id)
    result = await db.execute(query)
    driver = result.scalar()
    
    if not driver:
        return

    credits = driver.wallet_points
    old_tier = driver.tier
    new_tier = get_tier(credits)
    
    tier_weights = {"Bronze": 1, "Silver": 2, "Gold": 3, "Platinum": 4}
    
    if tier_weights.get(new_tier, 0) > tier_weights.get(old_tier, 0):
        success = send_rank_upgrade_email(
            user_email=driver.email or "driver@safedrive.com", 
            user_name=driver.owner_name or 'Driver', 
            old_rank=old_tier, 
            new_rank=new_tier
        )
        if success:
            driver.tier = new_tier
            await db.commit()

    # Update or Create Leaderboard Entry
    query_lb = select(Leaderboard).filter(Leaderboard.driver_id == driver_id)
    res_lb = await db.execute(query_lb)
    lb_entry = res_lb.scalar()
    
    if not lb_entry:
        lb_entry = Leaderboard(driver_id=driver_id)
        db.add(lb_entry)
    
    lb_entry.rank_score = float(credits)
    await db.commit()

    # Recalculate Positions
    query_all = select(Leaderboard).order_by(Leaderboard.rank_score.desc())
    res_all = await db.execute(query_all)
    all_entries = res_all.scalars().all()
    
    for index, entry in enumerate(all_entries):
        entry.rank_position = index + 1
    
    await db.commit()

