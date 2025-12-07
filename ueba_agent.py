# ueba_agent.py
import time
import json
import os

class UEBAAgent:
    def __init__(self, log_path="ueba_log.json"):
        self.log_path = log_path

        # Baseline allowed agent interactions:
        self.allowed_actions = {
            "DiagnosisAgent": ["send_to_master"],
            "MasterAgent": ["call_customer", "call_scheduler", "call_rca"],
            "CustomerAgent": ["notify_user"],
            "SchedulingAgent": ["recommend_slot"],
            "RCAAgent": ["generate_insight"]
        }

        # Event rate tracking
        self.event_times = []

        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                json.dump([], f)

        print("[UEBA] Security module initialized.")

    def log_event(self, agent, action):
        timestamp = time.time()
        self.event_times.append(timestamp)

        event = {
            "timestamp": timestamp,
            "agent": agent,
            "action": action
        }

        # Append log
        with open(self.log_path, "r+") as f:
            logs = json.load(f)
            logs.append(event)
            f.seek(0)
            json.dump(logs, f, indent=4)

        # Check for anomalies
        return self.analyze(agent, action)

    def analyze(self, agent, action):
        # 1. Unauthorized action
        if action not in self.allowed_actions.get(agent, []):
            return {
                "alert": True,
                "type": "UNAUTHORIZED_ACTION",
                "message": f"{agent} attempted unauthorized action: {action}"
            }

        # 2. Abnormal request frequency
        if len(self.event_times) > 5:
            if self.event_times[-1] - self.event_times[-5] < 1:  # 5 events in <1 sec
                return {
                    "alert": True,
                    "type": "RATE_SPIKE",
                    "message": "Abnormal high frequency of actions detected."
                }

        # 3. Normal
        return {"alert": False}
