# rca_capa_agent.py

import json
from ueba_agent import UEBAAgent
class RCACAPAAgent:
    def __init__(self, db_path="maintenance_db.json"):
        self.ueba = UEBAAgent()
        with open(db_path, "r") as f:
            self.db = json.load(f)
        print("[RCACAPA] Loaded historical maintenance database.")

    def analyze(self, diagnosis):
        component = diagnosis["likely_failure"]

        if component == "normal":
            return {
                "component": "normal",
                "insight": "No manufacturing action needed.",
                "severity": "none"
            }

        entry = self.db.get(component)

        if not entry:
            return {
                "component": component,
                "insight": "No RCA/CAPA data found.",
                "severity": "low"
            }

        insight = {
            "component": component,
            "historical_failures": entry["count"],
            "common_causes": entry["common_causes"],
            "repeated_models": entry["repeated_models"],
            "recommended_actions": entry["recommended_actions"],
            "severity": "high" if entry["count"] > 30 else "medium"
        }
        # UEBA logging
        if hasattr(self, "ueba"):
            self.ueba.log_event("RCACAPAAgent", "generate_insight")

        return insight
