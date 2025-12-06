# data_analysis_agent.py
# Real-Time Data Analysis Agent for EY Techathon
# Polls telematics API every 10 sec, keeps 30-reading window, computes features

import requests
import time
from collections import deque
import numpy as np

POLL_INTERVAL = 10          # seconds
WINDOW_SIZE = 10            # number of readings in rolling context window
TELEMATICS_URL = "http://localhost:8000/telematics/{}"


class DataAnalysisAgent:
    def __init__(self, maintenance_history=None):
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

        engine_temp = np.array([w["engine_temp"] for w in window])
        battery_voltage = np.array([w["battery_voltage"] for w in window])
        vibration = np.array([w["vibration"] for w in window])
        coolant = np.array([w["coolant_temp"] for w in window])

        # --- Maintenance history enrichment (for predictive maintenance) ---
        m_hist = self.maintenance_history.get(vehicle_id, {})
        last_service_km = m_hist.get("last_service_km", window[-1]["mileage"])
        last_service_days_ago = m_hist.get("last_service_days_ago", 0)
        num_repairs = m_hist.get("num_repairs", 0)
        last_failure_km = m_hist.get("last_failure_km", last_service_km)

        # Build feature dict
        features = {
            "vehicle_id": vehicle_id,

            # latest values
            "engine_temp": float(engine_temp[-1]),
            "battery_voltage": float(battery_voltage[-1]),
            "vibration": float(vibration[-1]),
            "coolant_temp": float(coolant[-1]),
            "dtc_code": window[-1]["dtc_code"],
            "mileage": window[-1]["mileage"],

            # rolling stats
            "engine_temp_avg": float(engine_temp.mean()),
            "engine_temp_std": float(engine_temp.std()),
            "battery_avg": float(battery_voltage.mean()),
            "battery_drop": float(battery_voltage[0] - battery_voltage[-1]),

            # trend features
            "temp_rise_rate": float(engine_temp[-1] - engine_temp[0]),
            "vibration_std": float(vibration.std()),
            "coolant_rise_rate": float(coolant[-1] - coolant[0]),

            # flags
            "dtc_flag": 1 if window[-1]["dtc_code"] != "P0000" else 0,
            "anomaly_flag": 1 if engine_temp[-1] > 105 or battery_voltage[-1] < 11.5 else 0,

            # maintenance / lifecycle context
            "last_service_km": float(last_service_km),
            "km_since_service": float(window[-1]["mileage"] - last_service_km),
            "last_service_days_ago": float(last_service_days_ago),
            "num_repairs": float(num_repairs),
            "last_failure_km": float(last_failure_km),
            "km_since_failure": float(window[-1]["mileage"] - last_failure_km),
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
            diagnosis_callback(features)

    def start(self, vehicle_list, diagnosis_callback):
        """Main real-time loop for all vehicles."""
        print("[DataAnalysisAgent] Real-time polling started.")

        while True:
            for vid in vehicle_list:
                self.run_once(vid, diagnosis_callback)

            time.sleep(POLL_INTERVAL)
