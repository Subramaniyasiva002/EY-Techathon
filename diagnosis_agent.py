# diagnosis_agent.py
import joblib, json
import numpy as np
from ueba_agent import UEBAAgent

class DiagnosisAgent:
    def __init__(self):
        self.ueba = UEBAAgent()
        self.model = joblib.load("models/rf_multiclass_model_updated.joblib")
        with open("models/rf_features.json") as f:
            self.feature_order = json.load(f)
        with open("models/rf_class_map.json") as f:
            self.class_map = json.load(f)

    def predict(self, features):
        # create input vector
        X = [[float(features.get(col, 0.0)) for col in self.feature_order]]
        X = np.array(X)

        # predict class
        cls = int(self.model.predict(X)[0])
        comp_name = self.class_map[str(cls)]

        # probability of failure = sum of non-normal classes
        probs = self.model.predict_proba(X)[0]
        failure_prob = 1 - probs[0]  # class 0 = normal

        # priority
        if failure_prob > 0.8:
            priority = "HIGH"
        elif failure_prob > 0.5:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # UEBA log
        if hasattr(self, "ueba"):
            self.ueba.log_event("DiagnosisAgent", "send_to_master")

        return {
            "vehicle_id": features["vehicle_id"],
            "risk_score": round(float(failure_prob), 3),
            "predicted_class": cls,
            "likely_failure": comp_name,
            "priority": priority,
            "eta_km": 150 if priority == "HIGH" else (300 if priority == "MEDIUM" else None)
        }
