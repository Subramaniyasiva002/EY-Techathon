# diagnosis_agent_backup.py - Backup Diagnosis Agent
"""
Backup Diagnosis Agent with limited capabilities
Can be run in SAFE MODE for security incidents
"""
import sys
import joblib
import numpy as np
from ueba_agent import UEBAAgent

class BackupDiagnosisAgent:
    def __init__(self, safe_mode=False):
        self.safe_mode = safe_mode
        self.agent_name = "DiagnosisAgent_BACKUP"
        
        # Load model
        try:
            self.model = joblib.load("models/ai4i_lgbm_model.joblib")  # Use base model as backup
            self.feature_order = joblib.load("models/feature_order.pkl")
            self.class_map = joblib.load("models/class_map.pkl")
        except:
            print(f"[{self.agent_name}] Warning: Could not load model files")
            self.model = None
        
        self.ueba = UEBAAgent()
        
        if safe_mode:
            print(f"[{self.agent_name}] Running in SAFE MODE (read-only)")
        else:
            print(f"[{self.agent_name}] Running as backup agent")
    
    def predict(self, features):
        """Predict with safety checks"""
        if self.safe_mode:
            print(f"[{self.agent_name}] SAFE MODE: Prediction only, no side effects")
        
        # UEBA check
        alert = self.ueba.log_event(self.agent_name, "predict")
        if not alert.get("allowed", True):
            print(f"[SECURITY] {self.agent_name} action blocked by UEBA")
            return None
        
        if not self.model:
            return self._fallback_prediction(features)
        
        try:
            # Feature engineering
            features["Power"] = features["Torque_Nm"] * features["Rotational_speed_rpm"] / 9550
            features["Strain"] = features["Tool_wear_min"] * features["Torque_Nm"]
            features["Temp_Diff"] = features["Process_temperature_K"] - features["Air_temperature_K"]
            
            # Prepare features
            X = np.array([[features[f] for f in self.feature_order]])
            
            # Predict
            pred_class = self.model.predict(X)[0]
            pred_proba = self.model.predict_proba(X)[0]
            
            risk_score = max(pred_proba)
            priority = "High" if risk_score > 0.8 else "Medium" if risk_score > 0.5 else "Low"
            
            return {
                "predicted_class": int(pred_class),
                "likely_failure": self.class_map.get(pred_class, "Unknown"),
                "risk_score": float(risk_score),
                "priority": priority,
                "backup_agent": True
            }
        except Exception as e:
            print(f"[{self.agent_name}] Prediction failed: {e}")
            return self._fallback_prediction(features)
    
    def _fallback_prediction(self, features):
        """Simple rule-based fallback"""
        if features.get("Process_temperature_K", 0) > 320:
            return {
                "predicted_class": 1,
                "likely_failure": "Heat Dissipation Failure",
                "risk_score": 0.8,
                "priority": "High",
                "backup_agent": True,
                "fallback": True
            }
        return {
            "predicted_class": 0,
            "likely_failure": "No Failure",
            "risk_score": 0.1,
            "priority": "Low",
            "backup_agent": True,
            "fallback": True
        }

if __name__ == "__main__":
    safe_mode = "--safe-mode" in sys.argv
    agent = BackupDiagnosisAgent(safe_mode=safe_mode)
    print(f"[{agent.agent_name}] Started and ready")
    
    # Keep running
    import time
    while True:
        time.sleep(60)
