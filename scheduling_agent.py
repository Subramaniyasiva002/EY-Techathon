# scheduling_agent.py
import numpy as np
from ueba_agent import UEBAAgent

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
        state = self.infer_demand_state(diagnosis)

        if self.Q is not None:
            action = np.argmax(self.Q[state])
        else:
            # fallback if RL not trained yet
            action = 1 if state == 2 else 3
        # UEBA logging
        if hasattr(self, "ueba"):
            self.ueba.log_event("SchedulingAgent", "recommend_slot")

        return {
            "vehicle_id": diagnosis["vehicle_id"],
            "recommended_slot": self.slot_map[action],
            "state": state,
            "action": action
        }
