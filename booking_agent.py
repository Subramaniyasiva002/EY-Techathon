import requests

class BookingAgent:
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url

    def get_slots(self):
        try:
            r = requests.get(f"{self.base_url}/slots")
            return r.json()["available_slots"]
        except:
            return []

    def book(self, vehicle_id: str, slot: str, method: str = "heuristic"):
        try:
            # We pass 'note' with the method to track how this booking was made
            payload = {"vehicle_id": vehicle_id, "slot": slot, "note": f"Booked via {method}"}
            r = requests.post(f"{self.base_url}/book", json=payload)
            return r.json()
        except:
            return {"status": "failed", "reason": "api_down"}