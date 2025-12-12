from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Service Center Booking API")

from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import uvicorn
from booking_queue import BookingQueue
from slots_manager import SlotsManager

app = FastAPI(title="Service Center Booking API (Async Queue)")

queue = BookingQueue()
slots_mgr = SlotsManager()

class BookingRequest(BaseModel):
    vehicle_id: str
    slot: str
    note: Optional[str] = None

@app.get("/slots")
def get_available_slots():
    # Read from persistent shared state
    available = slots_mgr.get_slots()
    return {"available_slots": available, "date": datetime.utcnow().date().isoformat()}

@app.post("/book")
def book_slot(booking: BookingRequest):
    # Producer: Push to Message Queue
    success = queue.enqueue(booking.vehicle_id, booking.slot, booking.note)
    
    if success:
        return {
            "status": "queued",
            "message": "Request accepted for processing",
            "vehicle_id": booking.vehicle_id,
            "slot": booking.slot
        }
    else:
        return {"status": "failed", "reason": "queue_error"}

@app.post("/complete")
def complete_service(slot: str):
    slots_mgr.release_slot(slot)
    return {"status": "slot_freed", "slot": slot}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)