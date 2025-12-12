import time
from booking_queue import BookingQueue
from slots_manager import SlotsManager

def run_worker():
    print("👷 Booking Worker Started... waiting for jobs.")
    queue = BookingQueue()
    slots_mgr = SlotsManager()

    while True:
        # Consumer: Poll Queue
        msg_id, payload = queue.dequeue()
        
        if payload:
            vid = payload["vehicle_id"]
            slot = payload["slot"]
            print(f"🔄 Processing booking for {vid} at {slot}...")
            
            # Simulated Processing Time (Smooth Load)
            time.sleep(1) 
            
            success, reason = slots_mgr.attempt_book(slot, vid)
            
            if success:
                print(f"✅ Slot Confirmed: {vid} -> {slot}")
                queue.mark_done(msg_id, "completed")
            else:
                print(f"❌ Booking Failed: {reason}")
                queue.mark_done(msg_id, "failed")
        else:
            time.sleep(1) # Idle Polling

if __name__ == "__main__":
    run_worker()
