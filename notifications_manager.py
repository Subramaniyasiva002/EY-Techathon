import json
import os
import time

DB_FILE = "notifications_db.json"

class NotificationsManager:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._save_db({})

    def _load_db(self):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_db(self, data):
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def add_notification(self, vehicle_id, message, likely_failure, recommended_slot, risk_score, priority, features=None):
        data = self._load_db()
        data[vehicle_id] = {
            "timestamp": time.time(),
            "message": message,
            "likely_failure": likely_failure,
            "recommended_slot": recommended_slot,
            "risk_score": risk_score,
            "priority": priority,
            "features": features, # Store features for conditional logging
            "status": "pending" # pending, booked, declined
        }
        self._save_db(data)
        
    def get_notification(self, vehicle_id):
        data = self._load_db()
        return data.get(vehicle_id)

    def update_notification_status(self, vehicle_id, status):
        data = self._load_db()
        if vehicle_id in data:
            data[vehicle_id]["status"] = status
            self._save_db(data)

    def clear_notification(self, vehicle_id):
        data = self._load_db()
        if vehicle_id in data:
            del data[vehicle_id]
            self._save_db(data)
