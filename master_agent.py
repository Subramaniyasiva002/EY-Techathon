from scheduling_agent import SchedulingAgent
from customer_agent import CustomerInteractionAgent
from rca_capa_agent import RCACAPAAgent
from ueba_agent import UEBAAgent
from booking_agent import BookingAgent
from feedback_agent import FeedbackAgent
import requests


# Initialize agents
sched = SchedulingAgent()
cust = CustomerInteractionAgent()
rca = RCACAPAAgent()
booker = BookingAgent()
fb = FeedbackAgent()
ueba = UEBAAgent()


# ============================================================
#   SCHEDULING STEP
# ============================================================
def scheduling_step(state):
    diagnosis = state["diagnosis"]
    vid = state["vehicle_id"]

    alert = ueba.log_event("MasterAgent", "call_scheduler")
    if alert["alert"]:
        print("\n🚨 UEBA ALERT:", alert["message"])
        return state

    # Logic Update: If predicted class is 0 (No Failure), do not schedule
    if diagnosis.get("predicted_class") == 0:
        print(f"\n[MasterAgent] Vehicle {vid} is healthy (Class 0). Scheduling skipped.")
        state["schedule"] = {"recommended_slot": None, "reason": "No Failure Detected"}
        return state

    # Logic Update: Check if already booked
    from slots_manager import SlotsManager
    sm = SlotsManager()
    is_booked, slot = sm.has_active_booking(vid)
    if is_booked:
        print(f"\n[MasterAgent] Vehicle {vid} already has a booked slot at {slot}. Scheduling skipped.")
        state["schedule"] = {"recommended_slot": None, "reason": "Already Booked", "existing_slot": slot}
        return state

    schedule = sched.recommend_slot(vid, diagnosis["risk_score"])
    state["schedule"] = schedule
    return state


# ============================================================
#   CUSTOMER INTERACTION STEP
# ============================================================
def customer_step(state):
    diagnosis = state["diagnosis"]
    schedule = state.get("schedule")

    msg = cust.generate_message(diagnosis, schedule)
    print("\n--- CUSTOMER MESSAGE ---")
    print(msg)

    # Logic Fix: Don't ask to book if no slot is recommended (Healthy or No Capacity)
    if not schedule or not schedule.get("recommended_slot"):
        print("\n[System] No booking slot available or required. Skipping booking.")
        state["confirmed"] = False
        return state

    # ASYNC HANDOFF: Post notification to dashboard instead of blocking terminal
    from notifications_manager import NotificationsManager
    nm = NotificationsManager()
    
    nm.add_notification(
        state["vehicle_id"], 
        msg, 
        diagnosis["likely_failure"], 
        schedule.get("recommended_slot"),
        diagnosis["risk_score"],
        diagnosis["priority"],
        features=state.get("features")
    )
    
    print("\n[Master] 🔔 Notification sent to Customer Dashboard.")
    print(f"Please check 'customer_dashboard.py' to approve booking for {schedule.get('recommended_slot')}.")
    
    state["confirmed"] = False # Defer booking to UI
    state["async_handoff"] = True # Signal that this is NOT a rejection
    return state


# ============================================================
#   BOOKING STEP
# ============================================================
def booking_step(state):
    # Async Handoff: If logic was deferred to dashboard, skip this step
    if state.get("async_handoff"):
        print("[Master] Booking logic deferred to Dashboard. Async Handoff complete.")
        return state

    if not state.get("confirmed"):
        print("\nCustomer declined service.")
        # Log negative feedback for RL training
        vid = state["vehicle_id"]
        diagnosis = state["diagnosis"]
        slot = state.get("schedule", {}).get("recommended_slot")
        fb.record_rejection(vid, diagnosis, slot)
        return state

    vid = state["vehicle_id"]
    slot = state["schedule"]["recommended_slot"]
    method = state["schedule"].get("method", "heuristic")

    result = booker.book(vid, slot, method)
    print("\nBOOKING RESULT:", result)

    state["booking"] = result

    # Async Queue Handling: 'queued' is also a valid positive state
    if result["status"] in ["success", "queued"]:
        print(f"\n[Master] Booking accepted (Status: {result['status']}). Worker will process it.")
    else:
        print(f"\n[Master] Booking rejected (Status: {result['status']}).")

    return state


# ============================================================
#   FEEDBACK STEP
# ============================================================
def feedback_step(state):
    booking = state.get("booking")
    # Accept 'queued' as valid for logging purposes in this simulation
    if not booking or booking.get("status") not in ["success", "queued"]:
        return state

    vid = state["vehicle_id"]
    diagnosis = state["diagnosis"]

    log = fb.record_service(vid, booking, diagnosis)
    state["service_log"] = log

    print("\n--- SERVICE LOGGED ---")
    print(log)

    print("\n--- SERVICE LOGGED ---")
    print(log)

    print("\n[Master] Service booked. Please complete service and provide feedback via the Dashboard.")
    print("Go to: Streamlit Dashboard > Customer Feedback")

    return state


# ============================================================
#   RCA / CAPA STEP
# ============================================================
def rca_step(state):
    diagnosis = state["diagnosis"]

    insights = rca.analyze(diagnosis)
    state["insights"] = insights

    print("\n--- MANUFACTURING INSIGHTS ---")
    print(insights)

    return state
