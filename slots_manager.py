import json
import os
import time

DB_FILE = "slots_db.json"

DEFAULT_SLOTS = {
    "09:00 AM": None,
    "10:00 AM": None,
    "11:00 AM": None,
    "12:00 PM": None,
    "02:00 PM": None,
    "04:00 PM": None,
}

class SlotsManager:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._save_db(DEFAULT_SLOTS)

    def _load_db(self):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_SLOTS

    def _save_db(self, data):
        # In a real system, use file locking (e.g. portalocker) here
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_slots(self):
        data = self._load_db()
        return [slot for slot, vid in data.items() if vid is None]

    def attempt_book(self, slot, vehicle_id):
        data = self._load_db()
        
        if slot not in data:
            return False, "invalid_slot"
        
        if data[slot] is not None:
            if data[slot] == vehicle_id:
                return False, "already_booked_by_you"
            return False, "slot_taken"

        data[slot] = vehicle_id
        self._save_db(data)
        return True, "booked"

    def release_slot(self, slot):
        data = self._load_db()
        if slot in data:
            data[slot] = None
            self._save_db(data)

    def has_active_booking(self, vehicle_id):
        data = self._load_db()
        for slot, booked_vid in data.items():
            if booked_vid == vehicle_id:
                return True, slot
        return False, None
