# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from reward_api import RewardSystemAPI
import uvicorn

# 1. Initialize the Server and your Reward API
app = FastAPI(title="SafeDrive Rewards Platform", version="1.0.0")
platform = RewardSystemAPI()

# 2. Define Request Models (Data Validation)
class TrafficEventRequest(BaseModel):
    plate_id: str
    action_key: str
    intersection_id: str = "PUNE_CENTER_01"

class RedemptionRequest(BaseModel):
    plate_id: str
    reward_key: str

class RegistrationRequest(BaseModel):
    plate_id: str
    vehicle_type: str

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "online", "platform": "Traffic Safety Rewards"}

@app.post("/register")
def register_vehicle(req: RegistrationRequest):
    return platform.register_user(req.plate_id, req.vehicle_type)

@app.get("/profile/{plate_id}")
def get_profile(plate_id: str):
    profile = platform.get_driver_profile(plate_id)
    if "status" in profile and profile["status"] == "error":
        raise HTTPException(status_code=404, detail="Driver not found")
    return profile

@app.post("/record-event")
def record_event(req: TrafficEventRequest):
    result = platform.record_traffic_event(req.plate_id, req.action_key, req.intersection_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.post("/convert-points/{plate_id}")
def trigger_midnight_batch(plate_id: str):
    """Simulates the midnight conversion process for a specific user."""
    return platform.run_midnight_batch(plate_id)

@app.post("/redeem")
def redeem_reward(req: RedemptionRequest):
    result = platform.request_redemption(req.plate_id, req.reward_key)
    if result.get("status") == "denied":
        raise HTTPException(status_code=402, detail=result.get("message"))
    return result

@app.get("/health")
def readiness_check():
    return {"status": "ready"}

if __name__ == "__main__":
    # Run the server on localhost:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)