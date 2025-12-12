import streamlit as st
import requests
import pandas as pd
import json
import time
from datetime import datetime
from slots_manager import SlotsManager
from feedback_agent import FeedbackAgent

# Page Config
st.set_page_config(page_title="Service Center & Feedback Hub", layout="wide")

# Initialize Helpers
sm = SlotsManager()
fb = FeedbackAgent()
BOOKING_API_URL = "http://localhost:9000"

st.title("🚗 Automotive Service Hub")

# Service Center Only View
st.header("🛠️ Service Center Operations")
st.write("Manage active bookings and complete services.")

# Refresh Button
if st.button("Refresh Slots"):
    st.rerun()

# Load Slots
slots_data = sm._load_db() # Accessing internal DB for full view

# Convert to DataFrame for display
active_bookings = []
for slot, vid in slots_data.items():
    predicted_issue = "-"
    if vid:
        # Lookup prediction from maintenance history
        hist = fb.db.get(vid, [])
        if hist:
            predicted_issue = hist[-1].get("likely_failure", "Unknown")
            
        active_bookings.append({
            "Slot": slot, 
            "Vehicle ID": vid, 
            "Predicted Issue": predicted_issue, 
            "Status": "Service In Progress"
        })
    else:
        active_bookings.append({
            "Slot": slot, 
            "Vehicle ID": "-", 
            "Predicted Issue": "-", 
            "Status": "Available"
        })
        
df = pd.DataFrame(active_bookings)
st.table(df)

# Action Section
st.subheader("Complete Service")
active_slots = [s for s, v in slots_data.items() if v is not None]

if active_slots:
    col1, col2 = st.columns(2)
    
    with col1:
        target_slot = st.selectbox("Select Slot to Complete", active_slots)
        
    vehicle_id = slots_data[target_slot]
    
    # Fetch Predicted Issue for display
    predicted_failure = "Unknown"
    hist = fb.db.get(vehicle_id, [])
    if hist:
        predicted_failure = hist[-1].get("likely_failure", "Unknown")
    
    with col2:
        st.info(f"**Vehicle:** {vehicle_id} | **Predicted:** {predicted_failure}")
    
    # Technician Input for True Label
    true_label = st.text_input("Enter Actual Failure Found (True Label)", value=predicted_failure)
    
    if st.button(f"Mark {target_slot} as Completed"):
        # 1. Call API to free slot
        try:
            r = requests.post(f"{BOOKING_API_URL}/complete", params={"slot": target_slot})
            if r.status_code == 200:
                st.success(f"✅ Slot {target_slot} freed successfully.")
                
                # 2. Update True Label with Technician Input
                fb.update_true_label(vehicle_id, true_label)
                st.info(f"📝 True Label recorded: {true_label}")
                
                # 3. Mark Service as Completed for Customer Feedback
                fb.mark_service_completed(vehicle_id)
                st.info("✅ Service status updated to 'Completed'. Customer notified for feedback.")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to call Booking API.")
        except Exception as e:
            st.error(f"API Error: {e}")
else:
    st.info("No active vehicle services at the moment.")

# -------------------------------------------------------------------
# MODEL REFINEMENT SECTION
# -------------------------------------------------------------------
st.divider()
st.header("🧠 Model Refinement")
st.write("Retrain the diagnosis model with live feedback data.")

# Count labeled samples
import csv
try:
    with open("live_feature_samples.csv", "r") as f:
        rows = list(csv.reader(f))
        # Skip header, count rows with actual_failure (last column not empty)
        labeled_count = sum(1 for row in rows[1:] if len(row) > 12 and row[12].strip())
except:
    labeled_count = 0

col1, col2 = st.columns([2, 1])

with col1:
    st.metric("Labeled Samples Collected", labeled_count)
    
    if labeled_count < 50:
        st.info(f"📊 Collect {50 - labeled_count} more samples to enable refinement (Recommended: 50-100)")
    else:
        st.success(f"✅ {labeled_count} samples ready! You can now refine the model.")

with col2:
    if labeled_count >= 50:
        if st.button("🚀 Refine Model Now", type="primary"):
            with st.spinner("Training refined model..."):
                import subprocess
                result = subprocess.run(
                    ["python", "refinement_train_new_model.py"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    st.success("✅ Model refinement complete!")
                    st.code(result.stdout[-500:], language="text")  # Show last 500 chars
                    st.info("Restart the diagnosis agent to use the refined model.")
                else:
                    st.error("❌ Refinement failed. Check logs.")
                    st.code(result.stderr, language="text")
    else:
        st.button("🚀 Refine Model Now", disabled=True, help=f"Need {50 - labeled_count} more samples")

