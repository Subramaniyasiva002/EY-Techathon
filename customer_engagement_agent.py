# customer_engagement_agent.py
# Customer Engagement Agent for EY Techathon
# Personalized chatbot to explain predicted issues and recommend service

from datetime import datetime
from typing import Dict, List, Optional


class CustomerEngagementAgent:
    """
    Chatbot agent that:
    - Explains predicted issues from telematics analysis
    - Provides personalized service recommendations
    - Engages vehicle owners in natural conversation
    """

    def __init__(self):
        self.conversation_history = {}  # {vehicle_id: [messages]}
        self.service_recommendations = {}

    def analyze_issues(self, features: Dict) -> List[str]:
        """
        Analyze features and identify issues that need explanation.
        Returns a list of issue descriptions.
        """
        issues = []

        # Check anomaly flag
        if features.get("anomaly_flag", 0) == 1:
            issues.append("anomaly_detected")

        # Check DTC code
        if features.get("dtc_flag", 0) == 1:
            dtc_code = features.get("dtc_code", "Unknown")
            issues.append(f"dtc_code_{dtc_code}")

        # Check engine temperature
        engine_temp = features.get("engine_temp", 0)
        engine_temp_avg = features.get("engine_temp_avg", 0)
        if engine_temp > 105 or engine_temp_avg > 100:
            issues.append("high_engine_temp")

        # Check battery
        battery_voltage = features.get("battery_voltage", 0)
        battery_avg = features.get("battery_avg", 0)
        if battery_voltage < 11.5 or battery_avg < 11.7:
            issues.append("low_battery")

        # Check vibration
        vibration_std = features.get("vibration_std", 0)
        if vibration_std > 0.6:
            issues.append("high_vibration")

        # Check service interval
        km_since_service = features.get("km_since_service", 0)
        days_since_service = features.get("last_service_days_ago", 0)
        if km_since_service > 10000 or days_since_service > 180:
            issues.append("service_overdue")

        return issues

    def generate_explanation(self, issue: str, features: Dict) -> str:
        """Generate personalized explanation for a specific issue."""
        vehicle_id = features.get("vehicle_id", "your vehicle")

        explanations = {
            "anomaly_detected": (
                f"🚨 **Anomaly Detected in {vehicle_id}**\n\n"
                "Our predictive maintenance system has detected unusual patterns in your vehicle's sensor data. "
                "This could indicate a developing issue that should be addressed proactively to prevent unexpected breakdowns."
            ),
            "dtc_code_P0420": (
                f"⚠️ **Diagnostic Trouble Code (DTC) Detected**\n\n"
                f"Your vehicle {vehicle_id} has triggered diagnostic code **P0420** (Catalyst System Efficiency Below Threshold). "
                "This typically indicates an issue with the catalytic converter or oxygen sensors. "
                "While your vehicle may still be drivable, this should be inspected soon to maintain emissions compliance and fuel efficiency."
            ),
            "high_engine_temp": (
                f"🌡️ **Elevated Engine Temperature**\n\n"
                f"Your vehicle {vehicle_id} is showing elevated engine temperatures "
                f"(current: {features.get('engine_temp', 0):.1f}°C, average: {features.get('engine_temp_avg', 0):.1f}°C). "
                "This could indicate:\n"
                "- Cooling system issues (low coolant, faulty thermostat)\n"
                "- Blocked radiator or cooling passages\n"
                "- Water pump malfunction\n\n"
                "Continued operation at high temperatures can cause engine damage."
            ),
            "low_battery": (
                f"🔋 **Battery Voltage Concern**\n\n"
                f"Your vehicle {vehicle_id} is showing low battery voltage "
                f"(current: {features.get('battery_voltage', 0):.2f}V, average: {features.get('battery_avg', 0):.2f}V). "
                "This suggests:\n"
                "- Battery may be aging or losing capacity\n"
                "- Alternator may not be charging properly\n"
                "- Electrical system drain\n\n"
                "A weak battery can lead to starting problems, especially in cold weather."
            ),
            "high_vibration": (
                f"📳 **Excessive Vibration Detected**\n\n"
                f"Your vehicle {vehicle_id} is experiencing higher-than-normal vibration levels "
                f"(standard deviation: {features.get('vibration_std', 0):.3f}). "
                "Possible causes:\n"
                "- Unbalanced tires or wheels\n"
                "- Worn suspension components\n"
                "- Engine mount issues\n"
                "- Driveshaft or CV joint problems\n\n"
                "Excessive vibration affects ride comfort and can indicate mechanical wear."
            ),
            "service_overdue": (
                f"🔧 **Service Interval Reminder**\n\n"
                f"Your vehicle {vehicle_id} has traveled **{features.get('km_since_service', 0):,.0f} km** "
                f"and **{features.get('last_service_days_ago', 0):.0f} days** since the last service. "
                "Regular maintenance helps:\n"
                "- Prevent unexpected breakdowns\n"
                "- Maintain fuel efficiency\n"
                "- Preserve vehicle value\n"
                "- Ensure safety\n\n"
                "We recommend scheduling a service appointment soon."
            ),
        }

        # Default explanation for unknown issues
        default = (
            f"⚠️ **Maintenance Alert for {vehicle_id}**\n\n"
            "Our monitoring system has detected a condition that may require attention. "
            "We recommend scheduling a service appointment for a professional inspection."
        )

        return explanations.get(issue, default)

    def generate_recommendation(self, issues: List[str], features: Dict) -> Dict:
        """
        Generate personalized service recommendations based on detected issues.
        Returns a dict with priority, urgency, and recommended actions.
        """
        vehicle_id = features.get("vehicle_id", "Unknown")
        priority = "normal"
        urgency = "scheduled"
        actions = []

        # Determine priority based on issues
        if "anomaly_detected" in issues or "high_engine_temp" in issues:
            priority = "high"
            urgency = "soon"
            actions.append("Schedule service appointment within 1-2 weeks")
            actions.append("Avoid long trips until inspected")
        elif "low_battery" in issues or "dtc_code" in issues:
            priority = "medium"
            urgency = "soon"
            actions.append("Schedule service appointment within 2-4 weeks")
        elif "high_vibration" in issues:
            priority = "medium"
            urgency = "scheduled"
            actions.append("Schedule service appointment at your convenience")
        elif "service_overdue" in issues:
            priority = "normal"
            urgency = "scheduled"
            actions.append("Schedule routine maintenance service")

        # Add specific service recommendations
        if "high_engine_temp" in issues:
            actions.append("Inspect cooling system (coolant level, thermostat, water pump)")
        if "low_battery" in issues:
            actions.append("Test battery and alternator charging system")
        if "high_vibration" in issues:
            actions.append("Check tire balance, suspension, and engine mounts")
        if "dtc_code_P0420" in issues:
            actions.append("Diagnose and repair catalytic converter or oxygen sensor system")

        # If no specific issues, recommend routine maintenance
        if not actions:
            actions.append("Continue regular maintenance schedule")
            actions.append("Monitor vehicle performance")

        return {
            "vehicle_id": vehicle_id,
            "priority": priority,
            "urgency": urgency,
            "recommended_actions": actions,
            "estimated_cost_range": self._estimate_cost_range(issues),
            "next_service_km": features.get("mileage", 0) + 5000,
        }

    def _estimate_cost_range(self, issues: List[str]) -> str:
        """Estimate cost range for service based on issues."""
        if "high_engine_temp" in issues or "anomaly_detected" in issues:
            return "$200 - $800"
        elif "dtc_code" in issues:
            return "$300 - $1,200"
        elif "low_battery" in issues:
            return "$150 - $400"
        elif "high_vibration" in issues:
            return "$100 - $600"
        elif "service_overdue" in issues:
            return "$100 - $300"
        return "$50 - $200"

    def generate_conversation_message(
        self, features: Dict, greeting: bool = False
    ) -> str:
        """
        Generate a personalized conversation message for the vehicle owner.
        """
        vehicle_id = features.get("vehicle_id", "your vehicle")
        issues = self.analyze_issues(features)
        recommendation = self.generate_recommendation(issues, features)

        if greeting:
            message = (
                f"👋 **Hello! I'm your Vehicle Health Assistant.**\n\n"
                f"I've been monitoring {vehicle_id} and have some important information to share with you.\n\n"
            )
        else:
            message = (
                f"📊 **Latest Analysis for {vehicle_id}**\n\n"
            )

        # Add issue explanations
        if issues:
            message += "**Issues Detected:**\n\n"
            for issue in issues:
                message += self.generate_explanation(issue, features) + "\n\n"
        else:
            message += (
                f"✅ **Good News!**\n\n"
                f"Your vehicle {vehicle_id} is operating normally. "
                f"No immediate issues detected. Continue with regular maintenance.\n\n"
            )

        # Add recommendations
        message += "**Recommended Actions:**\n\n"
        for i, action in enumerate(recommendation["recommended_actions"], 1):
            message += f"{i}. {action}\n"

        message += f"\n**Priority:** {recommendation['priority'].upper()}\n"
        message += f"**Urgency:** {recommendation['urgency']}\n"
        message += f"**Estimated Cost:** {recommendation['estimated_cost_range']}\n"

        return message

    def add_to_conversation(self, vehicle_id: str, message: str, role: str = "assistant"):
        """Add a message to the conversation history."""
        if vehicle_id not in self.conversation_history:
            self.conversation_history[vehicle_id] = []
        
        self.conversation_history[vehicle_id].append({
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_conversation_history(self, vehicle_id: str) -> List[Dict]:
        """Get conversation history for a vehicle."""
        return self.conversation_history.get(vehicle_id, [])

    def _generate_response_to_query(self, user_query: str, features: Dict) -> str:
        """
        Generate a response to a user query based on current vehicle analysis.
        This is a simple rule-based response system (can be enhanced with LLM).
        """
        query_lower = user_query.lower()
        vehicle_id = features.get("vehicle_id", "your vehicle")
        issues = self.analyze_issues(features)

        # Handle common queries
        if any(word in query_lower for word in ["problem", "issue", "wrong", "wrong with"]):
            if issues:
                response = f"Based on the latest analysis of {vehicle_id}, I've detected the following issues:\n\n"
                for issue in issues:
                    response += self.generate_explanation(issue, features) + "\n\n"
            else:
                response = f"✅ Great news! No issues detected with {vehicle_id}. Your vehicle is operating normally."
            return response

        elif any(word in query_lower for word in ["service", "maintenance", "repair", "fix"]):
            recommendation = self.generate_recommendation(issues, features)
            response = f"**Service Recommendations for {vehicle_id}:**\n\n"
            response += f"**Priority:** {recommendation['priority'].upper()}\n"
            response += f"**Urgency:** {recommendation['urgency']}\n"
            response += f"**Estimated Cost:** {recommendation['estimated_cost_range']}\n\n"
            response += "**Recommended Actions:**\n"
            for i, action in enumerate(recommendation['recommended_actions'], 1):
                response += f"{i}. {action}\n"
            return response

        elif any(word in query_lower for word in ["battery", "voltage"]):
            battery_voltage = features.get("battery_voltage", 0)
            battery_avg = features.get("battery_avg", 0)
            if "low_battery" in issues:
                return self.generate_explanation("low_battery", features)
            else:
                return (
                    f"Your vehicle's battery is operating normally. "
                    f"Current voltage: {battery_voltage:.2f}V, Average: {battery_avg:.2f}V. "
                    "No immediate concerns detected."
                )

        elif any(word in query_lower for word in ["temperature", "temp", "engine temp", "overheating"]):
            engine_temp = features.get("engine_temp", 0)
            if "high_engine_temp" in issues:
                return self.generate_explanation("high_engine_temp", features)
            else:
                return (
                    f"Your engine temperature is within normal range. "
                    f"Current: {engine_temp:.1f}°C. No cooling system issues detected."
                )

        elif any(word in query_lower for word in ["vibration", "shaking", "rough"]):
            if "high_vibration" in issues:
                return self.generate_explanation("high_vibration", features)
            else:
                return "Vibration levels are normal. No issues detected with your vehicle's balance or suspension."

        elif any(word in query_lower for word in ["cost", "price", "expensive", "how much"]):
            recommendation = self.generate_recommendation(issues, features)
            return (
                f"Based on the detected issues, estimated service cost range: **{recommendation['estimated_cost_range']}**. "
                "This is an estimate and actual costs may vary. I recommend contacting a service center for a detailed quote."
            )

        elif any(word in query_lower for word in ["urgent", "emergency", "critical", "safe to drive"]):
            recommendation = self.generate_recommendation(issues, features)
            if recommendation['priority'] == "high":
                return (
                    "⚠️ **This requires attention soon.** While your vehicle may still be drivable, "
                    "I recommend scheduling service within 1-2 weeks to prevent potential breakdowns. "
                    "Avoid long trips until inspected."
                )
            elif recommendation['priority'] == "medium":
                return (
                    "Your vehicle should be inspected within 2-4 weeks. "
                    "It's generally safe to drive for normal use, but don't delay service."
                )
            else:
                return (
                    "✅ Your vehicle is safe to drive. No urgent issues detected. "
                    "Continue with regular maintenance as scheduled."
                )

        else:
            # Default response
            return (
                f"I'm here to help with questions about {vehicle_id}. "
                "You can ask me about:\n"
                "- Issues or problems detected\n"
                "- Service recommendations\n"
                "- Battery or engine temperature\n"
                "- Vibration concerns\n"
                "- Cost estimates\n"
                "- Whether it's safe to drive\n\n"
                "Or click 'Show Service Recommendations' for a detailed report."
            )

