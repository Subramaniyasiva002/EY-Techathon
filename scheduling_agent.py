import numpy as np
import json
from datetime import datetime
from booking_agent import BookingAgent

class SchedulingAgent:
    def __init__(self):
        self.booker = BookingAgent()
        self.slot_list = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]
        try:
            self.Q = np.load("models/q_table.npy")
            print("[SchedulingAgent] RL model loaded – smart scheduling active")
        except:
            self.Q = None
            print("[SchedulingAgent] No RL model → using safe fallback")

    def get_demand_state(self, risk_score: float) -> int:
        if risk_score > 0.75:  return 2   # urgent
        if risk_score > 0.45:  return 1   # medium
        return 0                                 # normal

    def recommend_slot(self, vehicle_id: str, risk_score: float) -> dict:
        available = self.booker.get_slots()

        if not available:
            return {"recommended_slot": None, "reason": "no_slots_today"}

        if self.Q is not None:
            state = self.get_demand_state(risk_score)
            # pick best action only among available slots
            action_values = self.Q[state]
            best_action_idx = np.argmax(action_values)
            best_slot = self.slot_list[best_action_idx]

            if best_slot in available:
                return {"recommended_slot": best_slot, "method": "RL"}
            # if best RL slot taken → pick best available using same values
            candidates = [(i, self.slot_list[i]) for i in range(6) if self.slot_list[i] in available]
            best_idx = max(candidates, key=lambda x: action_values[x[0]])[1]
            return {"recommended_slot": best_idx, "method": "RL-fallback"}

        # Safe heuristic fallback
        preferred = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]
        for slot in preferred:
            if slot in available:
                return {"recommended_slot": slot, "method": "heuristic"}
        return {"recommended_slot": available[0], "method": "heuristic"}