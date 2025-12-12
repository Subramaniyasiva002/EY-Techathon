# customer_agent.py
# Updated for AI4I failure classes

from ueba_agent import UEBAAgent

class CustomerInteractionAgent:
    def __init__(self):
        self.ueba = UEBAAgent()
        print("[CustomerAgent] Ready (AI4I version).")

    def generate_message(self, diagnosis, schedule=None):
        vehicle_id = diagnosis.get("vehicle_id", "Unknown")
        failure = diagnosis.get("likely_failure", "No Failure")
        priority = diagnosis.get("priority", "LOW")

        # -------------------------------------------------------------
        # EXPLANATION MAPPING BASED ON AI4I FAILURE CLASSES
        # -------------------------------------------------------------
        explanations = {
            "No Failure": "Your vehicle is operating normally with no abnormal patterns detected.",
            
            "Heat Dissipation Failure":
                "We detected overheating patterns in the engine/process temperature. This may cause performance loss or unexpected shutdown if not serviced soon.",
            
            "Power/Battery Failure":
                "We observed abnormal torque or process load patterns which correlate with power system issues. This may lead to stall or startup failure.",
            
            "Tool Wear/Vibration Failure":
                "High tool wear or vibration patterns were detected. This can lead to mechanical imbalance or reduced lifespan of moving components.",
            
            "Overstrain Failure":
                "Your vehicle shows signs of mechanical overstrain. Continuous use under this condition may lead to component fatigue or sudden failure."
        }

        # Handle unknown class gracefully
        reason = explanations.get(failure, "We detected an anomaly requiring attention.")

        # -------------------------------------------------------------
        # PRIORITY-BASED MESSAGE TONE
        # -------------------------------------------------------------
        if failure == "No Failure":
            urgency = "😊 No immediate action is required."
        else:
            if priority == "HIGH":
                urgency = "⚠️ This requires immediate attention to avoid a breakdown."
            elif priority == "MEDIUM":
                urgency = "ℹ️ We recommend scheduling a preventive service soon."
            else:
                urgency = "🙂 This is a low-risk observation. No urgent action needed."

        # -------------------------------------------------------------
        # BASE MESSAGE FORMATION
        # -------------------------------------------------------------
        msg = (
            f"Hello! Here is the latest health update for your vehicle **{vehicle_id}**.\n\n"
            f"**Issue Detected:** {failure}\n"
            f"**Details:** {reason}\n"
            f"{urgency}\n"
        )

        # -------------------------------------------------------------
        # Add scheduling suggestion (if schedule is recommended)
        # -------------------------------------------------------------
        if schedule and schedule.get("recommended_slot"):
            slot = schedule.get("recommended_slot")
            msg += f"\nWould you like to book a service slot at **{slot}**?"
        elif schedule and schedule.get("existing_slot"):
            slot = schedule.get("existing_slot")
            msg += f"\n✅ **Reminder:** You already have a confirmed booking at **{slot}**."

        # -------------------------------------------------------------
        # UEBA security logging
        # -------------------------------------------------------------
        alert = self.ueba.log_event("CustomerAgent", "notify_user")

        if alert["alert"]:
            print("\n🚨 UEBA ALERT (CustomerAgent):", alert["message"])
            print("→ Customer messaging halted for safety.")
            return "Security Alert: Customer message not sent."

        return msg

    def customer_confirm(self, confirmed: bool):
        """Called from master agent after customer responds."""
        if confirmed:
            return "Customer has confirmed the service booking."
        else:
            return "Customer declined the service. We will monitor and notify again if needed."
