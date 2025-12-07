# scheduling_agent.py
import numpy as np
from ueba_agent import UEBAAgent
import json
from datetime import datetime


class SchedulingAgent:
    def __init__(self, q_table_path="models/q_table.npy"):
        self.ueba = UEBAAgent()
        try:
            self.Q = np.load(q_table_path)
            print("[SchedulingAgent] Q-table loaded successfully.")
        except:
            # fallback: no RL model available
            self.Q = None
            print("[SchedulingAgent] Q-table not found. Using fallback scheduling.")


        self.forecast = self.load_forecast()
        self.capacity_per_day = 15  # example: each center can handle 15 bookings/day
        
        # map action index to actual service time
        self.slot_map = {
            0: "09:00 AM",
            1: "10:00 AM",
            2: "11:00 AM",
            3: "12:00 PM",
            4: "01:00 PM",
            5: "02:00 PM",
        }

    def infer_demand_state(self, diagnosis):
        """
        Determine demand state based on risk or vehicle priority.
        You can replace with real service center load.
        """
        risk = diagnosis["risk_score"]

        if risk > 0.75:  
            return 2     # high demand handling (urgent)
        elif risk > 0.45:
            return 1     # medium
        return 0         # low

    def choose_slot(self, diagnosis):
        slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]
        today = datetime.utcnow().date()
        
        selected = slots[1]  # default slot
        
        # Check forecast
        overloaded = self.is_day_overloaded(str(today))
        
        if overloaded:
            print("[SchedulingAgent] ⚠️ Forecast indicates overload today. Using alternate time.")
            selected = "04:00 PM"  # choose a low-demand slot

        return {
            "vehicle_id": diagnosis["vehicle_id"],
            "recommended_slot": selected,
            "forecast_overload": overloaded
        }

    def load_forecast(self, path="service_forecast.json"):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return None

    def is_day_overloaded(self, date_str):
        if not self.forecast:
            return False
        
        day_value = self.forecast["national_forecast"].get(date_str, 0)
        
        return day_value > self.capacity_per_day

