# rca_capa_agent.py - Outer Loop Manufacturing Insights

import json
from collections import Counter
from datetime import datetime

class RCACAPAAgent:
    def __init__(self, db_path="maintenance_history_db.json"):
        self.db_path = db_path
        self.insights_file = "manufacturing_insights.json"

    def load_db(self):
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except:
            return {}

    def generate_outer_loop_insight(self):
        """Auto-triggered after 8-10 services -> Manufacturing Quality Insights"""
        db = self.load_db()
        
        # Collect all completed services across ALL vehicles
        all_services = []
        for vehicle_id, records in db.items():
            if vehicle_id.startswith("_"): 
                continue  # skip metadata
            for record in records:
                if record.get("status") == "Completed":
                    all_services.append({
                        "vehicle_id": vehicle_id,
                        "failure": record.get("likely_failure", "Unknown"),
                        "risk_score": record.get("risk_score", 0.0),
                        "priority": record.get("priority", "LOW"),
                        "slot": record.get("slot", ""),
                        "feedback": record.get("customer_feedback", {}),
                        "timestamp": record.get("timestamp", "")
                    })

        total_vehicles_serviced = len({s["vehicle_id"] for s in all_services})
        total_services = len(all_services)

        if total_services < 8:
            return None

        # === REAL RCA (Root Cause Analysis) ===
        failures = [s["failure"] for s in all_services if s["failure"] not in ["normal", "No Failure", ""]]
        if not failures:
            return {"insight": "No critical failures in this batch", "severity": "none"}

        failure_counts = Counter(failures)
        top_failure = failure_counts.most_common(1)[0]
        failure_name, count = top_failure

        high_priority_cases = sum(1 for s in all_services if s["priority"] == "HIGH")
        avg_risk = sum(s["risk_score"] for s in all_services) / total_services
        
        # Calculate average customer satisfaction
        ratings = [s["feedback"].get("rating", 5) for s in all_services if s["feedback"]]
        avg_rating = sum(ratings) / len(ratings) if ratings else 5.0

        # === AI4I-Specific CAPA Recommendations ===
        capa_recommendations = {
            "Heat Dissipation Failure": {
                "root_cause": "Insufficient cooling capacity under high load conditions",
                "capa": "Upgrade thermal interface material + add passive heat spreader to motor housing",
                "process_change": "Increase thermal paste application thickness from 0.5mm to 0.8mm",
                "expected_reduction": "35-45%"
            },
            "Power/Battery Failure": {
                "root_cause": "Excessive power draw causing voltage sag",
                "capa": "Implement power limiting algorithm + upgrade to higher C-rate cells",
                "process_change": "Add pre-production power stress test (2x rated load for 10min)",
                "expected_reduction": "40-50%"
            },
            "Tool Wear/Vibration Failure": {
                "root_cause": "Premature tool degradation due to material hardness mismatch",
                "capa": "Switch to carbide-tipped tools + implement predictive replacement schedule",
                "process_change": "Reduce tool engagement depth by 15% and increase feed rate compensation",
                "expected_reduction": "25-35%"
            },
            "Overstrain Failure": {
                "root_cause": "Torque spikes exceeding design limits during startup",
                "capa": "Implement soft-start ramp profile + reinforce drive shaft coupling",
                "process_change": "Add torque sensor calibration step to production line (Station 7)",
                "expected_reduction": "30-40%"
            }
        }

        capa_data = capa_recommendations.get(failure_name, {
            "root_cause": "Unknown - requires detailed investigation",
            "capa": "Initiate quality investigation with field samples",
            "process_change": "TBD pending RCA completion",
            "expected_reduction": "15-25%"
        })

        insight = {
            "generated_at": datetime.utcnow().isoformat(),
            "batch_summary": f"{total_services} services from {total_vehicles_serviced} vehicles",
            "top_recurring_defect": failure_name,
            "occurrences": count,
            "fleet_impact_percent": round(count / total_services * 100, 1),
            "high_priority_cases": high_priority_cases,
            "avg_risk_score": round(avg_risk, 3),
            "avg_customer_rating": round(avg_rating, 2),
            "root_cause": capa_data["root_cause"],
            "capa_recommendation": capa_data["capa"],
            "process_change": capa_data["process_change"],
            "expected_defect_reduction": capa_data["expected_reduction"],
            "severity": "CRITICAL" if count >= 7 else "HIGH" if count >= 4 else "MEDIUM",
            "action": "Immediate R&D + Quality escalation" if count >= 6 else "Monitor next batch",
            "all_failure_types": dict(failure_counts)
        }

        # Save to manufacturing insights file
        try:
            with open(self.insights_file, "r") as f:
                insights_history = json.load(f)
        except:
            insights_history = []
        
        insights_history.append(insight)
        
        with open(self.insights_file, "w") as f:
            json.dump(insights_history, f, indent=4)

        # Print beautiful report
        print("\n" + "=" * 70)
        print("MANUFACTURING QUALITY INSIGHTS - OUTER LOOP ACTIVATED")
        print("=" * 70)
        print(f"Batch size           : {total_services} services ({total_vehicles_serviced} vehicles)")
        print(f"Top defect           : {failure_name} ({count} cases)")
        print(f"Fleet impact         : {insight['fleet_impact_percent']}%")
        print(f"Customer satisfaction: {insight['avg_customer_rating']}/5.0")
        print(f"\nROOT CAUSE:")
        print(f"  {capa_data['root_cause']}")
        print(f"\nCAPA RECOMMENDATION:")
        print(f"  {capa_data['capa']}")
        print(f"\nPROCESS CHANGE:")
        print(f"  {capa_data['process_change']}")
        print(f"\nExpected reduction   : {capa_data['expected_reduction']}")
        print(f"Severity             : {insight['severity']}")
        print(f"Action required      : {insight['action']}")
        print("=" * 70)

        return insight

    def analyze(self, diagnosis):
        """Legacy method for single-diagnosis analysis"""
        return {
            "insight": f"Diagnosed: {diagnosis.get('likely_failure', 'Unknown')}",
            "recommendation": "Monitor fleet trends"
        }
