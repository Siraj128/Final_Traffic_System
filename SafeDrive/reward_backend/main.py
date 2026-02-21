from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database.connection import engine, Base
from routes import auth, wallet, card, events, notifications, leaderboard, redemption, benefits, analytics, admin, user, assistant, vehicles
import uvicorn
import asyncio

# Create Tables (Async)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(
    title="SafeDrive Rewards API",
    description="Backend for Reward Wallet & Traffic Management System",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await init_db()

# CORS (Allow all for hackathon/dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")
app.include_router(card.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(redemption.router, prefix="/api")
app.include_router(benefits.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")

# Serve Admin Dashboard
app.mount("/admin-panel", StaticFiles(directory="static/admin", html=True), name="admin")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return {"message": "SafeDrive Rewards Backend is Running (Async Mode)"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
