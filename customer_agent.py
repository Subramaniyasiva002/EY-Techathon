# customer_agent.py
from ueba_agent import UEBAAgent

class CustomerInteractionAgent:
    def __init__(self):
        self.ueba = UEBAAgent()
        print("[CustomerAgent] Ready.")

    def generate_message(self, diagnosis, schedule=None):
        vid = diagnosis["vehicle_id"]
        risk = diagnosis["risk_score"]
        comp = diagnosis["likely_failure"]
        priority = diagnosis["priority"]

        base_msg = f"Hello! We detected early signs of a possible *{comp}* issue in your vehicle {vid}.\n"

        # Persuasive explanations
        if comp == "cooling_failure":
            reason = "The engine temperature trend shows overheating which may cause engine shutdown."
        elif comp == "battery_failure":
            reason = "The battery voltage is dropping faster than normal, which may result in starting problems."
        elif comp == "vibration_failure":
            reason = "High vibration patterns indicate a possible suspension or wheel bearing issue."
        elif comp == "engine_stress":
            reason = "Engine stress patterns suggest wear that may affect long-term performance."
        else:
            reason = "We detected some irregular patterns which may require inspection."

        # Priority-based messaging
        if priority == "HIGH":
            urgency = "⚠️ This requires immediate attention to avoid a breakdown."
        elif priority == "MEDIUM":
            urgency = "ℹ️ We recommend scheduling a preventive service soon."
        else:
            urgency = "😊 Your vehicle is operating normally. No urgent action needed."

        msg = f"{base_msg}{reason}\n{urgency}"

        # If schedule is suggested:
        if schedule:
            slot = schedule["recommended_slot"]
            msg += f"\n\nWould you like to book a service slot at **{slot}**?"
        # UEBA logging
        if hasattr(self, "ueba"):
            self.ueba.log_event("CustomerAgent", "notify_user")

        return msg

    def customer_confirm(self, confirmed: bool):
        if confirmed:
            return "Customer confirmed booking."
        return "Customer declined. Will remind later."
