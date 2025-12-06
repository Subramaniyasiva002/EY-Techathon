# telematics_api.py
# Clean, Real-Time Telematics Mock API for EY Techathon

from fastapi import FastAPI
import random, time
from datetime import datetime

app = FastAPI(title="Real-Time Telematics API")

# 10 vehicles: VH001 ... VH010
VEHICLES = [f"VH{i:03d}" for i in range(1, 11)]


@app.get("/")
def home():
    return {
        "message": "Telematics API running",
        "vehicles": VEHICLES,
        "example": "/telematics/VH001"
    }


@app.get("/telematics/{vehicle_id}")
def get_telematics(vehicle_id: str):
    if vehicle_id not in VEHICLES:
        return {"error": "Invalid vehicle ID (use VH001–VH010)"}

    # Inject anomalies only for two vehicles (for demo)
    anomaly = vehicle_id in ["VH005", "VH008"]

    reading = {
        "vehicle_id": vehicle_id,
        "timestamp": time.time(),
        "iso_time": datetime.utcnow().isoformat(),

        # core engine + battery signals
        "engine_temp": random.uniform(82, 98) if not anomaly else random.uniform(105, 120),
        "coolant_temp": random.uniform(75, 95) if not anomaly else random.uniform(95, 110),
        "battery_voltage": random.uniform(12.2, 13.0) if not anomaly else random.uniform(10.5, 11.2),
        "vibration": random.uniform(0.1, 0.4) if not anomaly else random.uniform(0.9, 1.4),

        # contextual features
        "speed": random.uniform(0, 80),
        "rpm": random.randint(700, 3500),
        "mileage": random.randint(15000, 80000),

        # fault information
        "dtc_code": "P0000" if not anomaly else "P0420",
        "has_anomaly": anomaly
    }

    return reading
