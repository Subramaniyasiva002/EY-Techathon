# master_agent.py

class MasterAgent:
    def __init__(self):
        print("[MasterAgent] Ready.")

    def handle_diagnosis(self, diagnosis):
        vid = diagnosis["vehicle_id"]
        risk = diagnosis["risk_score"]
        prio = diagnosis["priority"]

        print("\n=========================")
        print(f" MASTER AGENT DECISION FOR {vid}")
        print("=========================")
        print("Risk Score:", risk)
        print("Priority. :", prio)
        print("Component :", diagnosis["likely_failure"])

        # === HIGH PRIORITY (urgent) ===
        if prio == "HIGH":
            print("⚠️  URGENT FAILURE Likely! Booking immediate service...")
            # Here you will call: scheduling_agent.book(vid)
            return "URGENT_SERVICE"

        # === MEDIUM PRIORITY ===
        elif prio == "MEDIUM":
            print("⚠️  Recommend Preventive Check Soon.")
            return "ADVISORY"

        # === LOW PRIORITY ===
        else:
            print("✓ Vehicle Normal. No action needed.")
            return "NO_ACTION"
