# data_analysis_agent.py
# Real-Time Data Analysis Agent for EY Techathon
# Polls telematics API every 10 sec, keeps 30-reading window, computes features

import requests
import time
from collections import deque
import numpy as np
from ueba_agent import UEBAAgent
POLL_INTERVAL = 3          # seconds
WINDOW_SIZE = 10            # number of readings in rolling context window
TELEMATICS_URL = "http://localhost:8000/telematics/{}"


class DataAnalysisAgent:
    def __init__(self, maintenance_history=None):
        self.ueba = UEBAAgent()
        self.windows = {}   # {vehicle_id: deque}
        # Optional: static or periodically refreshed maintenance history per vehicle
        # Example structure:
        # {
        #   "VH001": {
        #       "last_service_km": 45000,
        #       "last_service_days_ago": 60,
        #       "num_repairs": 3,
        #       "last_failure_km": 42000
        #   },
        #   ...
        # }
        self.maintenance_history = maintenance_history or {}

    def _init_window(self, vehicle_id):
        if vehicle_id not in self.windows:
            self.windows[vehicle_id] = deque(maxlen=WINDOW_SIZE)

    def get_reading(self, vehicle_id):
        """Fetch one reading from telematics API."""
        try:
            r = requests.get(TELEMATICS_URL.format(vehicle_id), timeout=5)
            return r.json()
        except Exception as e:
            print(f"[ERROR] Failed to get telematics for {vehicle_id}: {e}")
            return None

    def add_to_window(self, vehicle_id, reading):
        self.windows[vehicle_id].append(reading)

    def is_window_ready(self, vehicle_id):
        return len(self.windows[vehicle_id]) == WINDOW_SIZE

    def compute_features(self, vehicle_id):
        """Extract meaningful features from 30 readings."""
        window = list(self.windows[vehicle_id])

        # AI4I fields
        air_temp = np.array([w["Air_temperature_K"] for w in window])
        proc_temp = np.array([w["Process_temperature_K"] for w in window])
        rpm = np.array([w["Rotational_speed_rpm"] for w in window])
        torque = np.array([w["Torque_Nm"] for w in window])
        tool_wear = np.array([w["Tool_wear_min"] for w in window])
        
        # Ensure we capture Type so we can pass it to the model if needed (encoded as 0,1,2)
        machine_type = window[-1]["Type"]

        # --- Maintenance history enrichment (placeholder logic preserved) ---
        m_hist = self.maintenance_history.get(vehicle_id, {})
        # Note: 'mileage' is no longer in the standard AI4I fields, 
        # so we depend on provided history or default to 0 for now.
        last_service_time = m_hist.get("last_service_time", 0) 
        
        # Build feature dict matching model expectations (roughly)
        features = {
            "timestamp": window[-1]["timestamp"],
            "vehicle_id": vehicle_id,
            "Type": machine_type,
            
            # Latest values
            "Air_temperature_K": float(air_temp[-1]),
            "Process_temperature_K": float(proc_temp[-1]),
            "Rotational_speed_rpm": float(rpm[-1]),
            "Torque_Nm": float(torque[-1]),
            "Tool_wear_min": float(tool_wear[-1]),

            # Rolling stats (Engineering features)
            "proc_temp_avg": float(proc_temp.mean()),
            "rpm_std": float(rpm.std()),
            "torque_avg": float(torque.mean()),
            "torque_std": float(torque.std()),
            "wear_rate": float(tool_wear[-1] - tool_wear[0]),

            # Anomaly flag for ground truth monitoring
            "has_anomaly": window[-1].get("has_anomaly", False)
        }

        return features

    def run_once(self, vehicle_id, diagnosis_callback):
        """Fetch → store → compute (if ready) → send for diagnosis."""
        self._init_window(vehicle_id)

        reading = self.get_reading(vehicle_id)
        if reading:
            self.add_to_window(vehicle_id, reading)

        if self.is_window_ready(vehicle_id):
            # Optional: show the full context window used for analysis
            window_context = list(self.windows[vehicle_id])
            print(f"\n[CONTEXT WINDOW] Last {WINDOW_SIZE} readings for {vehicle_id}:")
            print(window_context)

            features = self.compute_features(vehicle_id)
            # UEBA log
            if hasattr(self, "ueba"):
                self.ueba.log_event("DataAnalysisAgent", "send_window")

            diagnosis_callback(features)

    def start(self, vehicle_list, diagnosis_callback):
        """Main real-time loop for all vehicles."""
        print("[DataAnalysisAgent] Real-time polling started.")

        while True:
            for vid in vehicle_list:
                self.run_once(vid, diagnosis_callback)

            time.sleep(POLL_INTERVAL)
