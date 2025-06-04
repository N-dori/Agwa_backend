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
    timestamp: datetime

class Pod(BaseModel):
    id: str
    age: int

class Classification(BaseModel):
    status: str
    classification: str

class Unit(BaseModel):
    id: str
    pods: List[Pod]
    classification:Optional[Classification] = None
    readings: List[Reading]



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
        if unit.readings:
            last_reading = unit.readings[-1]
            is_valid = validate_reading(last_reading)
            unit.classification = Classification(
                    status= "OK",
                    classification= "Healthy" if is_valid else "Needs Attention"
            )
            sensor_store.append({
            "unitId": unit.id,
            "timestamp": last_reading.timestamp.isoformat(),
            "readings": last_reading.dict(),
            "classification": unit.classification.dict()
            })
            

    # Save full units into memory as dicts
    sensor_units_store.extend([unit.dict() for unit in units])
    return units

# -------- GET Alerts Endpoint --------
@app.get("/api/alerts")
def get_problematic_readings(unitId: str = Query(...)):
    selected_unit = next((u for u in sensor_units_store if u["id"] == unitId), None)
    if not selected_unit:
        return []

    problematic_readings = []
    for reading in selected_unit["readings"]:
        if reading["pH"] < 5.5 or reading["pH"] > 7.0:
            problematic_readings.append({
                "id": reading["id"],
                "pH": reading["pH"],
                "temp": reading["temp"],
                "ec": reading["ec"],
                 "timestamp": reading["timestamp"].isoformat() if hasattr(reading["timestamp"], "isoformat") else reading["timestamp"]
            })

    sorted_alerts = sorted(problematic_readings, key=lambda r: r["timestamp"], reverse=True)
    return sorted_alerts[:10]
