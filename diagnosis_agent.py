# diagnosis_agent.py
import joblib
import pandas as pd
import numpy as np
from ueba_agent import UEBAAgent

class DiagnosisAgent:
    def __init__(self):
        self.ueba = UEBAAgent()
        
        # Load the new AI4I-specific model
        try:
            self.model = joblib.load("models/ai4i_lgbm_refined.joblib")
            print("[DiagnosisAgent] Loaded models/ai4i_lgbm_refined.joblib")
        except Exception as e:
            print(f"[DiagnosisAgent] Error loading model: {e}")
            self.model = None

        # Define feature order expected by the model (matches new_train.py)
        self.feature_order = [
            "Type", 
            "Air_temperature_K", 
            "Process_temperature_K", 
            "Rotational_speed_rpm", 
            "Torque_Nm", 
            "Tool_wear_min",
            "Power_W",
            "Strain_Index",
            "Temp_Diff"
        ]

        # Map predicted class integers to human-readable failure types
        self.class_map = {
            0: "No Failure",
            1: "Heat Dissipation Failure",
            2: "Power/Battery Failure",
            3: "Tool Wear/Vibration Failure",
            4: "Overstrain Failure"
        }

    def predict(self, features):
        if not self.model:
            return {"error": "Model not loaded"}
        
        # 0. Feature Engineering (On-The-Fly)
        # We must compute the same derived features used in training
        rpm = features.get("Rotational_speed_rpm", 0)
        torque = features.get("Torque_Nm", 0)
        wear = features.get("Tool_wear_min", 0)
        proc_temp = features.get("Process_temperature_K", 0)
        air_temp = features.get("Air_temperature_K", 0)

        features["Power_W"] = torque * rpm * 0.1047
        features["Strain_Index"] = torque * wear
        features["Temp_Diff"] = proc_temp - air_temp

        # 1. Align features to model input format
        # Fix: Use DataFrame to avoid "X does not have valid feature names" warning
        input_data = {col: [features.get(col, 0)] for col in self.feature_order}
        X = pd.DataFrame(input_data)

        # 2. Predict Classification
        pred_class = int(self.model.predict(X)[0])
        failure_type = self.class_map.get(pred_class, "Unknown Issue")

        # 3. Get Probability for Priority Assignment
        # Assuming model.predict_proba returns [prob_class_0, prob_class_1, ...]
        probs = self.model.predict_proba(X)[0]
        
        # risk_score = probability of ANY failure (1 - prob of No Failure)
        risk_score = 1.0 - probs[0]

        # 4. Assign Priority
        if risk_score > 0.75:
            priority = "HIGH"
            eta_km = 100
        elif risk_score > 0.45:
            priority = "MEDIUM"
            eta_km = 300
        else:
            priority = "LOW"
            eta_km = None

        # UEBA Logging
        if hasattr(self, "ueba"):
            self.ueba.log_event("DiagnosisAgent", "diagnosis_complete")

        return {
            "vehicle_id": features.get("vehicle_id", "Unknown"),
            "risk_score": round(risk_score, 3),
            "predicted_class": pred_class,
            "likely_failure": failure_type,
            "priority": priority,
            "eta_km": eta_km,
            "timestamp": features.get("timestamp")
        }
