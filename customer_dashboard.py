import streamlit as st
import requests
import time
from notifications_manager import NotificationsManager
from feedback_agent import FeedbackAgent

# Page Config
st.set_page_config(page_title="Customer Booking & Feedback", layout="centered")

nm = NotificationsManager()
fb = FeedbackAgent()
BOOKING_API_URL = "http://localhost:9000"

st.title("📱 Customer Vehicle App")

# 1. Login
known_vehicles = list(fb.db.keys()) if fb.db.keys() else ["VH001", "VH003", "VH005"]
vehicle_id = st.selectbox("Select Your Vehicle ID", known_vehicles)

if vehicle_id:
    st.divider()
    
    # 2. Check for Active Alerts (Booking Request)
    notification = nm.get_notification(vehicle_id)
    
    if notification:
        status = notification.get("status", "pending")
        
        # ---------------------------------------------------------
        # STATE 1: PENDING (User needs to approve)
        # ---------------------------------------------------------
        if status == "pending":
            st.subheader("🔔 New Health Alert")
            st.warning(notification["message"])
            st.write(f"**Recommended Slot:** {notification['recommended_slot']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Book Service"):
                    # Call Booking API
                    payload = {
                        "vehicle_id": vehicle_id,
                        "slot": notification["recommended_slot"],
                        "note": "Customer Confirmed via App"
                    }
                    try:
                        r = requests.post(f"{BOOKING_API_URL}/book", json=payload)
                        if r.status_code == 200:
                            st.success("Booking Confirmed! Techician has been notified.")

                            # CONDITIONAL LOGGING: Save features only now that booked
                            features = notification.get("features")
                            
                            # Construct objects for saving
                            booking_info = {
                                "slot": notification["recommended_slot"],
                                "booking_id": f"BKG-{int(time.time())}" # Mock ID
                            }
                            diagnosis_info = {
                                "likely_failure": notification["likely_failure"],
                                "risk_score": notification.get("risk_score", 0.0), # Retrieved from notification
                                "priority": notification.get("priority", "HIGH")
                            }

                            if features:
                                from sample_store import SampleStore
                                ss = SampleStore()
                                # Reconstruct diagnosis dict for saving features
                                diag_for_sample = diagnosis_info.copy()
                                diag_for_sample["predicted_class"] = 1
                                ss.save_sample(features, diag_for_sample)
                                print(f"Sample saved for {vehicle_id} upon booking.")
                            
                            # CRITICAL: Record Service in DB so it shows up as "Booked"
                            fb.record_service(vehicle_id, booking_info, diagnosis_info)
                            
                            # Update Status to BOOKED (do not clear yet)
                            nm.update_notification_status(vehicle_id, "booked")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Booking Failed: {r.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
                        
            with col2:
                if st.button("❌ No, Decline"):
                    fb.record_rejection(
                        vehicle_id, 
                        {"likely_failure": notification["likely_failure"], "risk_score": 0.0}, 
                        notification["recommended_slot"]
                    )
                    st.info("Booking Declined.")
                    nm.clear_notification(vehicle_id)
                    time.sleep(2)
                    st.rerun()

        # ---------------------------------------------------------
        # STATE 2: BOOKED (Waiting for Service)
        # ---------------------------------------------------------
        elif status == "booked":
            st.subheader("🛠️ Service Status")
            st.info(f"Service booked for **{notification['recommended_slot']}**. Vehicle is at the center.")
            
            # CRITICAL FIX: Reload database to see technician's completion status
            with open(fb.db_path, "r") as f:
                import json
                fb.db = json.load(f)
            
            # Check if Service is Completed
            history = fb.db.get(vehicle_id, [])
            is_completed = False
            if history:
                 # Check the last entry. If status is 'Completed', move to feedback
                 if history[-1].get("status") == "Completed":
                     is_completed = True
            
            if is_completed:
                st.success("✅ Service Completed! Please provide feedback below.")
                st.write("---")
                st.write("### Rate Your Experience")
                with st.form("feedback_form"):
                    rating = st.slider("Rating", 1, 5, 5)
                    comments = st.text_area("Comments", "Great service!")
                    submitted = st.form_submit_button("Submit Feedback")
                    
                    if submitted:
                        fb.collect_feedback(vehicle_id, rating, comments)
                        st.success("Thank you for your feedback!")
                        # NOW we clear the notification cycle
                        nm.clear_notification(vehicle_id)
                        time.sleep(2)
                        st.rerun()
            else:
                 st.write("⏳ Technician is working on your vehicle... (Check back soon)")
                 if st.button("Check Status"):
                     st.rerun()
                
    else:
        st.info("No active health alerts. Your vehicle is running smoothly.")
