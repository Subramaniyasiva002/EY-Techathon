# booking_agent.py
import requests

class BookingAgent:
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url

    def book(self, vehicle_id, slot):
        payload = {"vehicle_id": vehicle_id, "slot": slot}
        try:
            r = requests.post(f"{self.base_url}/book", params=payload)
            return r.json()
        except:
            return {"status": "failed", "reason": "Booking API unreachable"}
