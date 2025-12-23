# telematics_api_ai4i_fixed.py
# Corrected AI4I-Compatible Telematics API (Value Ranges Match Dataset)

from fastapi import FastAPI
import random, time
from datetime import datetime

app = FastAPI(title="AI4I-Compatible Telematics API (Fixed Ranges)")

VEHICLES = [f"VH{i:03d}" for i in range(1, 11)]

@app.get("/")
def home():
    return {
        "message": "AI4I-Compatible Telematics API Running",
        "vehicles": VEHICLES,
        "example": "/telematics/VH001"
    }

@app.get("/telematics/{vehicle_id}")
def get_telematics(vehicle_id: str):
    if vehicle_id not in VEHICLES:
        return {"error": "Invalid vehicle ID"}

    # Vehicles with induced failures (Reduced frequency)
    # Default is Healthy. 20% chance of anomaly for testing flow.
    anomaly = False
    if vehicle_id in ["VH001", "VH005", "VH010"]:
        anomaly = random.random() < 0.5 # 50% chance of failure interaction

    # ----------------------------------------------------
    # NORMAL SENSOR RANGES (Real AI4I dataset)
    # ----------------------------------------------------
    air_temp = random.uniform(295, 315)
    proc_temp = air_temp + random.uniform(5, 12)
    rpm = random.randint(1400, 1900)
    torque = random.uniform(25, 45)
    tool_wear = random.uniform(0, 250)

    # ----------------------------------------------------
    # FAILURE SIMULATION (Realistic AI4I failure patterns)
    # ----------------------------------------------------
    if anomaly:
        failure_type = random.choice([
            "Heat Dissipation Failure",
            "Power/Battery Failure",
            "Tool Wear/Vibration Failure",
            "Overstrain Failure"
        ])

        if failure_type == "Heat Dissipation Failure":
            # Tuned: Diff < 8.6 is failure. Testing ~7.0.
            rpm = int(random.gauss(1340, 40))
            air_temp = random.gauss(302.5, 1.0)
            proc_temp = air_temp + random.gauss(7.0, 0.5)
            torque = random.gauss(52.3, 6.0)

        elif failure_type == "Power/Battery Failure":
            # Dataset: High variance. Targeting High Power mode for certainty.
            # Power > 9000W. 
            rpm = int(random.gauss(2400, 100))  # High RPM
            torque = random.gauss(60, 5.0)      # High Torque
            proc_temp = random.gauss(310, 1.0)

        elif failure_type == "Tool Wear/Vibration Failure":
            # Tuned: Wear > 230 is failure. Testing ~240.
            tool_wear = random.gauss(240, 5.0) 
            torque = random.gauss(40, 5.0)
            rpm = int(random.gauss(1580, 100))

        elif failure_type == "Overstrain Failure":
            # Dataset: RPM ~1350 (std 60), Torque ~58 (std 6), Wear ~207 (std 15)
            # Low RPM, High Torque, High Wear
            rpm = int(random.gauss(1350, 60))
            torque = random.gauss(58.5, 5.0)
            tool_wear = random.gauss(210, 15.0)
            proc_temp = random.gauss(310, 1.0)

    reading = {
        "vehicle_id": vehicle_id,
        "timestamp": time.time(),
        "iso_time": datetime.utcnow().isoformat(),

        # AI4I-derived sensor features
        "Air_temperature_K": air_temp,
        "Process_temperature_K": proc_temp,
        "Rotational_speed_rpm": rpm,
        "Torque_Nm": torque,
        "Tool_wear_min": tool_wear,

        "Type": random.choice([0, 1, 2]),   # encoded machine type
        "has_anomaly": anomaly
    }

    return reading
