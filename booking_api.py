# booking_api.py
from fastapi import FastAPI
import random

app = FastAPI(title="Mock Service Center Booking API")

# Store which vehicle booked which slot
# None = available
SLOTS = {
    "09:00 AM": None,
    "10:00 AM": None,
    "11:00 AM": None,
    "12:00 PM": None,
    "01:00 PM": None,
    "02:00 PM": None
}

@app.get("/slots")
def get_slots():
    """
    Return all available slots.
    A slot is available when its value is None.
    """
    available = [slot for slot, booked_by in SLOTS.items() if booked_by is None]
    return {"available_slots": available}


@app.post("/book")
def book_slot(vehicle_id: str, slot: str):
    """
    Book a slot for the given vehicle.
    Rules:
    - If the slot is invalid → fail
    - If the same vehicle tries again → allow
    - If another vehicle already booked it → fail
    - Otherwise → book the slot
    """
    if slot not in SLOTS:
        return {"status": "failed", "reason": "Invalid slot"}

    current = SLOTS[slot]

    # CASE 1: Same vehicle re-booking → ALLOW
    if current == vehicle_id:
        return {
            "status": "success",
            "vehicle_id": vehicle_id,
            "slot": slot,
            "booking_id": random.randint(10000, 99999),
            "note": "Re-booking allowed for same vehicle"
        }

    # CASE 2: Slot booked by another vehicle → BLOCK
    if current is not None and current != vehicle_id:
        return {
            "status": "failed",
            "reason": f"Slot already booked by {current}"
        }

    # CASE 3: Slot is free → BOOK IT
    SLOTS[slot] = vehicle_id

    return {
        "status": "success",
        "vehicle_id": vehicle_id,
        "slot": slot,
        "booking_id": random.randint(10000, 99999)
    }


@app.post("/complete")
def complete_service(slot: str):
    """
    Mark a service slot as completed and free the slot.
    This MUST be called by MasterAgent after service is finished.
    """
    if slot not in SLOTS:
        return {"status": "failed", "reason": "Invalid slot"}

    # reset slot to available
    SLOTS[slot] = None

    return {
        "status": "slot_reset",
        "slot": slot
    }
