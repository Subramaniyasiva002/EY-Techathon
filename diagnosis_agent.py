# diagnosis_agent.py
import joblib
import json
import numpy as np
import os

class DiagnosisAgent:
    def __init__(self, model_path="models/rf_model.joblib", feature_path="models/rf_features.json"):
        if not os.path.exists(model_path):
            raise FileNotFoundError("RandomForest model not found! Train model before running.")

        if not os.path.exists(feature_path):
            raise FileNotFoundError("rf_features.json not found!")

        # Load model + feature order
        self.model = joblib.load(model_path)
        with open(feature_path, "r") as f:
            self.feature_order = json.load(f)

        print("[DiagnosisAgent] RF model loaded.")
        print("[DiagnosisAgent] Feature order loaded:", self.feature_order)

    def predict(self, features: dict):
        """Convert feature dict into model input and return risk score."""
        X = []

        # Prepare model input in exact feature order
        for col in self.feature_order:
            X.append(float(features.get(col, 0.0)))

        X = np.array(X).reshape(1, -1)

        # Predict probability of failure
        prob = float(self.model.predict_proba(X)[0][1])

        # Priority & component inference
        if prob > 0.8:
            priority = "HIGH"
            comp = "Cooling/Battery"
        elif prob > 0.5:
            priority = "MEDIUM"
            comp = "Wear / Stress"
        else:
            priority = "LOW"
            comp = "Normal"

        return {
            "vehicle_id": features["vehicle_id"],
            "risk_score": round(prob, 3),
            "priority": priority,
            "likely_failure": comp,
            "eta_km": 200 if prob > 0.5 else None
        }
