from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Models --------
class Reading(BaseModel):
    id: str
    pH: float
    temp: float
    ec: float

class Pod(BaseModel):
    id: str
    readings: List[Reading]
    age: int
    timestamp: datetime
    status: Optional[str] = None
    classification: Optional[str] = None

class Unit(BaseModel):
    id: str
    pods: List[Pod]

# -------- In-Memory Stores --------
sensor_store = []  # Flattened last reading per pod
sensor_units_store = []  # Full raw unit data

# -------- Validation Logic --------
def validate_reading(reading: Reading) -> bool:
    return not (reading.pH < 5.5 or reading.pH > 7.0)

# -------- POST Endpoint --------
@app.post("/api/sensor")
def post_units(units: List[Unit]):
    for unit in units:
        for pod in unit.pods:
            if pod.readings:
                last_reading = pod.readings[-1]
                is_valid = validate_reading(last_reading)
                pod.status = "OK"
                pod.classification = "Healthy" if is_valid else "Needs Attention"

                sensor_store.append({
                    "unitId": unit.id,
                    "podId": pod.id,
                    "timestamp": pod.timestamp.isoformat(),
                    "readings": last_reading.dict(),
                    "classification": pod.classification
                })

    # Save full units into memory as dicts
    sensor_units_store.extend([unit.dict() for unit in units])
    return units

# -------- GET Alerts Endpoint --------
@app.get("/api/alerts")
def get_problematic_readings(unitId: str = Query(...)):
    # Find the unit
    selected_unit = next((u for u in sensor_units_store if u["id"] == unitId), None)
    if not selected_unit:
        return  []

    problematic_readings = []
    for pod in selected_unit["pods"]:
        for reading in pod["readings"]:
            # Manually validate since reading is a plain dict
            if reading["pH"] < 5.5 or reading["pH"] > 7.0:
                problematic_readings.append({
                    "unitId": unitId,
                    "podId": pod["id"],
                    "timestamp": pod["timestamp"],
                    "readings": reading,
                })

    # Sort by timestamp descending
    sorted_alerts = sorted(problematic_readings, key=lambda r: r["timestamp"], reverse=True)
    return  sorted_alerts[:10]
