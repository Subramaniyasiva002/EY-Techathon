# feedback_agent.py
import json
from datetime import datetime
import csv


class FeedbackAgent:
    def __init__(self, db_path="maintenance_history_db.json"):
        self.db_path = db_path
        with open(db_path, "r") as f:
            self.db = json.load(f)

    def record_service(self, vehicle_id, booking, diagnosis):
        """Log completed service in DB"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "slot": booking["slot"],
            "booking_id": booking["booking_id"],
            "likely_failure": diagnosis["likely_failure"],
            "risk_score": diagnosis["risk_score"],
            "priority": diagnosis["priority"]
        }

        self.db[vehicle_id].append(entry)

        # Save file
        with open(self.db_path, "w") as f:
            json.dump(self.db, f, indent=4)

        return entry

    def collect_feedback(self, vehicle_id, rating, comments):
        """Append customer feedback to last service"""
        if not self.db[vehicle_id]:
            return None

        self.db[vehicle_id][-1]["customer_feedback"] = {
            "rating": rating,
            "comments": comments
        }

        # Save file
        with open(self.db_path, "w") as f:
            json.dump(self.db, f, indent=4)

        return self.db[vehicle_id][-1]
    def update_true_label(self, vehicle_id, actual_label):
        rows = []
        with open("live_feature_samples.csv", "r") as f:
            rows = list(csv.reader(f))

        for i in range(len(rows)-1, 0, -1):
            vid = rows[i][1].strip()
            val = rows[i][-1].strip().lower()

            if vid == vehicle_id and val in ["", "none", "null"]:
                rows[i][-1] = actual_label
                break

        with open("live_feature_samples.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

