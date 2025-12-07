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

    alert = ueba.log_event("MasterAgent", "call_scheduler")
    if alert["alert"]:
        print("\n🚨 UEBA ALERT:", alert["message"])
        return state

    schedule = sched.choose_slot(diagnosis)
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

    ans = input("Book service? (y/n): ").strip().lower()
    state["confirmed"] = True if ans == "y" else False

    return state


# ============================================================
#   BOOKING STEP
# ============================================================
def booking_step(state):
    if not state.get("confirmed"):
        print("\nCustomer declined service.")
        return state

    vid = state["vehicle_id"]
    slot = state["schedule"]["recommended_slot"]

    result = booker.book(vid, slot)
    print("\nBOOKING RESULT:", result)

    state["booking"] = result

    if result["status"] == "success":
        requests.post("http://localhost:9000/complete", params={"slot": slot})

    return state


# ============================================================
#   FEEDBACK STEP
# ============================================================
def feedback_step(state):
    booking = state.get("booking")
    if not booking or booking.get("status") != "success":
        return state

    vid = state["vehicle_id"]
    diagnosis = state["diagnosis"]

    log = fb.record_service(vid, booking, diagnosis)
    state["service_log"] = log

    print("\n--- SERVICE LOGGED ---")
    print(log)

    rating = input("Rate service (1–5): ").strip()
    comments = input("Comments: ").strip()

    fb_data = fb.collect_feedback(vid, rating, comments)
    state["feedback"] = fb_data

    actual = diagnosis["likely_failure"]
    fb.update_true_label(vid, actual)

    print("TRUE LABEL SAVED:", actual)

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
