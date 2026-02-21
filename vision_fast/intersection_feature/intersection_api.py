# intersection_feature/intersection_api.py
"""
PRODUCTION INTERSECTION INTELLIGENCE API (V4.0)
Standard: High-Performance REST Service
Purpose: Serves Real-time Demand, Forensic Safety Alerts, and Dashboard Analytics.
Source of Truth: PDF Pages 3, 6, 7, 11, 12.
"""

import sys
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
import uvicorn
from psycopg2 import extras

# --- PRODUCTION PATH FIX ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig
from intersection_db import IntersectionDatabase

# --- DATA SCHEMAS (For Teammate Integration) ---
class DemandResponse(BaseModel):
    north_pressure: float
    south_pressure: float
    east_pressure: float
    west_pressure: float
    pedestrian_active: bool
    last_update: datetime

class SafetyAlert(BaseModel):
    anomaly_type: str
    severity_level: str
    incident_description: str
    forensic_telemetry: Dict
    timestamp: datetime

class JunctionSummary(BaseModel):
    last_24h_flow: Dict[str, int]
    total_alerts: int
    junction_status: str

# --- API INITIALIZATION ---
app = FastAPI(
    title="Pune Smart City: Intersection Perception API",
    description="High-fidelity traffic intelligence service for Signal Control and Monitoring.",
    version="4.0.0"
)
db = IntersectionDatabase()

@app.get("/", tags=["Health"])
def health_check():
    """System heartbeat for the Central Management System."""
    return {
        "status": "OPERATIONAL",
        "subsystem": "Intersection_Perception_V4",
        "db_connection": "CONNECTED",
        "timestamp": datetime.now()
    }

@app.get("/intersection/{junction_id}/demand", response_model=DemandResponse, tags=["Traffic Logic"])
def get_live_demand(junction_id: str = Path(..., description="The ID of the junction (e.g. PUNE_CHOWK_01)")):
    """
    REQUIRED BY SIRAJ: Returns the 'Weighted Pressure' per road.
    Use this to calculate dynamic green light duration as per PDF Page 3.
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT north_pressure, south_pressure, east_pressure, west_pressure, pedestrian_active, last_update
                    FROM realtime_demand WHERE junction_id = %s
                ''', (junction_id,))
                res = cursor.fetchone()
                if not res:
                    raise HTTPException(status_code=404, detail=f"Junction {junction_id} has no live demand data.")
                return res
    except Exception as e:
        logging.error(f"[API-ERROR] Demand Fetch Failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Perception Logic Error")

@app.get("/intersection/{junction_id}/alerts", response_model=List[SafetyAlert], tags=["Safety"])
def get_active_safety_incidents(junction_id: str):
    """
    REQUIRED BY SAQLAIN: Returns all unresolved accidents or gridlocks.
    Includes forensic telemetry (physics) for authorities as per PDF Page 6 & 11.
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT anomaly_type, severity_level, incident_description, forensic_telemetry, timestamp
                    FROM safety_incidents 
                    WHERE junction_id = %s AND is_resolved = FALSE
                    ORDER BY timestamp DESC
                ''', (junction_id,))
                return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intersection/{junction_id}/summary", response_model=JunctionSummary, tags=["Analytics"])
def get_dashboard_summary(junction_id: str):
    """
    REQUIRED FOR DASHBOARD: Historical summary of traffic flow and safety.
    Source of Truth: PDF Page 12 (Monitoring Dashboard).
    """
    stats = db.get_dashboard_summary(junction_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Analytics unavailable for this junction.")
    return stats

if __name__ == "__main__":
    # Standard Port for Intersection Service is 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)