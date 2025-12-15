import streamlit as st
import requests
import time
import json
from notifications_manager import NotificationsManager
from feedback_agent import FeedbackAgent

# Page Config
st.set_page_config(
    page_title="My - AutoHub",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("assets/custom.css")
except:
    pass

nm = NotificationsManager()
fb = FeedbackAgent()
BOOKING_API_URL = "http://localhost:9000"

# Helper function to reload feedback database
def reload_feedback_db():
    """Reload the feedback database to get latest data"""
    with open(fb.db_path, "r") as f:
        fb.db = json.load(f)

# --- SIDEBAR NAVIGATION (Mobile Friendly) ---
st.sidebar.markdown("""
    <div class="sidebar-logo">
        <span class="sidebar-logo-icon">🚗</span>
        <span class="sidebar-logo-text">My AutoHub</span>
    </div>
""", unsafe_allow_html=True)

menu_options = ["Overview", "Bookings", "Service History", "Profile"]
menu_icons = {"Overview": "🏠", "Bookings": "📅", "Service History": "📋", "Profile": "👤"}

selection = st.sidebar.radio(
    "Menu", 
    menu_options, 
    format_func=lambda x: f"{menu_icons[x]} {x}",
    label_visibility="collapsed"
)

# --- HEADER ---
# 1. Login Logic (Simulated)
known_vehicles = list(fb.db.keys()) if fb.db.keys() else ["VH001", "VH003", "VH005"]
vehicle_id = st.sidebar.selectbox("Active Vehicle", known_vehicles)

if not vehicle_id:
    st.warning("Please select a vehicle.")
    st.stop()

st.markdown(f"""
    <div class="dashboard-header" style="border-bottom:none; margin-bottom:10px;">
        <div class="header-left">
            <div>
                <h1 class="header-title">Hello, Alice 👋</h1>
                <p class="text-secondary" style="margin:0;">{vehicle_id} • Tesla Model 3</p>
            </div>
        </div>
        <div class="header-actions">
           <div class="status-badge">CONNECTED</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- PAGES ---

if selection == "Overview":
    # 2. Health Visualization
    notification = nm.get_notification(vehicle_id)
    risk_score = notification.get("risk_score", 0.0) if notification else 0.0
    health_score = int(100 - (risk_score * 100))
    health_pct = f"{health_score}%"
    health_color = "#10B981" if health_score > 80 else "#F59E0B" if health_score > 50 else "#EF4444"
    
    # CSS Variable Injection for Ring
    st.markdown(f"""
    <style>
        :root {{
            --health-color: {health_color};
            --health-pct: {health_pct};
        }}
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown(f"""
        <div class="customer-card" style="text-align:center;">
            <h3 class="kpi-label">System Health</h3>
            <div class="health-score-ring">
                <div class="health-value">{health_score}</div>
                <div class="health-label">Score</div>
            </div>
            <div style="font-weight:600; color:{health_color}; margin-top:10px;">
                { "ALL SYSTEMS OPTIMAL" if health_score > 80 else "ATTENTION REQUIRED" }
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Alerts Section
        if notification:
            status = notification.get("status", "pending")
            
            if status == "pending":
                st.markdown(f"""
                <div class="customer-card">
                    <h3 class="kpi-label" style="color:#EF4444; margin-bottom:15px;">⚠️ Active Alert</h3>
                    <div class="alert-card">
                        <div class="alert-icon">🔧</div>
                        <div class="alert-content">
                            <h4>{notification['likely_failure']} Detected</h4>
                            <p>{notification['message']}</p>
                            <div style="margin-top:10px; font-size:12px; opacity:0.8;">
                                Est. Repair Time: <strong>45 mins</strong>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action Buttons
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"📅 Book {notification['recommended_slot']}", type="primary", use_container_width=True):
                         # Call Booking API
                        payload = {
                            "vehicle_id": vehicle_id,
                            "slot": notification["recommended_slot"],
                            "note": "Customer App Confirmed"
                        }
                        try:
                            # Mock API call if server not running or just run it
                            r = requests.post(f"{BOOKING_API_URL}/book", json=payload)
                            
                            # SAVE RECORD (Logic preserved)
                            features = notification.get("features")
                            booking_info = {"slot": notification["recommended_slot"], "booking_id": f"B{int(time.time())}"}
                            diag_info = {
                                "likely_failure": notification["likely_failure"],
                                "risk_score": notification.get("risk_score", 0),
                                "priority": notification.get("priority", "HIGH")
                            }
                            if features:
                                from sample_store import SampleStore
                                ss = SampleStore()
                                diag_f = diag_info.copy()
                                diag_f["predicted_class"] = 1 
                                ss.save_sample(features, diag_f)
                                
                            fb.record_service(vehicle_id, booking_info, diag_info)
                            nm.update_notification_status(vehicle_id, "booked")
                            st.success("Booking Confirmed!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Connection Error: {e}")
                            
                with c2:
                    if st.button("Dismiss Alert", use_container_width=True):
                        nm.clear_notification(vehicle_id)
                        st.rerun()

            elif status == "booked":
                st.markdown("""
                <div class="customer-card">
                    <h3 class="kpi-label" style="color:#3B82F6;">🗓️ Upcoming Service</h3>
                    <div style="display:flex; align-items:center; gap:15px; margin-top:10px;">
                        <div style="font-size:40px;">📅</div>
                        <div>
                            <div style="font-weight:700; color:white; font-size:18px;">Tomorrow, 10:00 AM</div>
                            <div style="color:#9CA3AF;">Service Center A • Bay 3</div>
                        </div>
                    </div>
                    <div style="margin-top:20px; padding:10px; background:rgba(59, 130, 246, 0.1); border-radius:8px; font-size:13px; color:#60A5FA;">
                        Technicians are preparing for your arrival.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Check for completed services without feedback
            reload_feedback_db()  # Reload to get latest data
            hist = fb.db.get(vehicle_id, [])
            completed_without_feedback = [h for h in hist if h.get("status") == "Completed" and not h.get("customer_feedback")]
            
            if completed_without_feedback:
                latest_service = completed_without_feedback[-1]  # Get most recent
                st.markdown("""
                <div class="customer-card" style="border: 2px solid rgba(250, 204, 21, 0.3); background: rgba(250, 204, 21, 0.05);">
                    <h3 class="kpi-label" style="color:#FACC15; margin-bottom:15px;">💬 Service Feedback Requested</h3>
                    <p style="color:#E5E7EB; margin-bottom:15px;">We'd love to hear about your recent service experience!</p>
                    <div style="display:flex; gap:10px;">
                        <span style="color:#9CA3AF; font-size:13px;">Issue: </span>
                        <span style="color:#FACC15; font-weight:600;">{}</span>
                    </div>
                </div>
                """.format(latest_service.get('true_label', latest_service.get('likely_failure', 'Service'))), unsafe_allow_html=True)
                
                # Quick feedback form
                with st.form(key="quick_feedback_overview"):
                    col_fb1, col_fb2 = st.columns([1, 1])
                    with col_fb1:
                        rating = st.slider("Rating", 1, 5, 5, key="quick_rating")
                        stars_display = '⭐' * rating
                        st.markdown(f"""
                            <div style="text-align:center; padding:8px; background:rgba(250, 204, 21, 0.1); 
                                       border-radius:6px; margin:5px 0;">
                                <span style="font-size:20px; color:#FACC15;">{stars_display}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_fb2:
                        comment = st.text_area("Comments", key="quick_comment", height=80, 
                                              placeholder="Optional feedback...")
                    
                    if st.form_submit_button("💾 Submit Feedback", type="primary", use_container_width=True):
                        try:
                            fb.collect_feedback(vehicle_id, rating, comment)
                            reload_feedback_db()  # Reload after saving
                            st.success("✅ Thank you for your feedback!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                
        else:
             st.markdown("""
                <div class="customer-card">
                    <h3 class="kpi-label" style="color:#10B981;">✅ Status</h3>
                    <p style="color:#9CA3AF; margin-top:10px;">No active alerts. Your vehicle is running smoothly.</p>
                    <div style="margin-top:20px; padding:15px; background:rgba(16, 185, 129, 0.1); border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#34D399; font-weight:600;">Next Service</span>
                        <span style="color:white;">Sep 2025</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

elif selection == "Bookings":
    st.header("My Bookings")
    # Fetch history
    hist = fb.db.get(vehicle_id, [])
    # Filter for active
    active = [h for h in hist if h.get("status") in ["Booked", "Pending"]]
    
    if active:
        for booking in active:
            st.markdown(f"""
             <div class="customer-card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; color:white;">Booking #{booking.get('booking_id', 'N/A')}</span>
                    <span class="status-pill servicing">ACTIVE</span>
                </div>
                <div style="margin-top:10px; color:#9CA3AF;">
                    Slot: <b style="color:white;">{booking.get('slot')}</b>
                </div>
                <div style="margin-top:5px; color:#9CA3AF;">
                    Issue: <span style="color:#FACC15;">{booking.get('likely_failure')}</span>
                </div>
             </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active bookings.")

elif selection == "Service History":
    st.header("Service History")
    # Reload database to get latest feedback data
    reload_feedback_db()
    hist = fb.db.get(vehicle_id, [])
    completed = [h for h in hist if h.get("status") == "Completed"]

    if completed:
        for idx, service in enumerate(completed):
            service_timestamp = service.get('timestamp', 'Recent Service')
            # Format timestamp if it's ISO format
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(service_timestamp.replace('Z', '+00:00'))
                service_timestamp = dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
            
            issue_resolved = service.get('true_label', service.get('likely_failure', 'Unknown'))
            feedback = service.get('customer_feedback')
            has_feedback = feedback is not None and isinstance(feedback, dict) and feedback.get('rating') is not None
            
            st.markdown(f"""
             <div class="customer-card">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div style="flex:1;">
                        <div style="font-weight:700; color:white; font-size:18px;">Service Completed</div>
                        <div style="color:#9CA3AF; font-size:13px; margin-top:5px;">{service_timestamp}</div>
                    </div>
                    <span class="status-pill" style="background:#064E3B; color:#34D399; border:1px solid #065F46;">COMPLETED</span>
                </div>
                <div style="margin-top:15px; color:#9CA3AF;">
                    Issue Resolved: <b style="color:white;">{issue_resolved}</b>
                </div>
            """, unsafe_allow_html=True)
            
            # Show existing feedback or feedback form
            if has_feedback:
                rating = feedback.get('rating', 0)
                comments = feedback.get('comments', '') or ''
                stars = '⭐' * int(rating) if rating else ''
                st.markdown(f"""
                    <div style="margin-top:15px; padding:15px; background:rgba(34, 197, 94, 0.1); 
                               border:1px solid rgba(34, 197, 94, 0.3); border-radius:8px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                            <span style="color:#22C55E; font-weight:600;">Your Feedback:</span>
                            <span style="color:#FACC15; font-size:18px;">{stars}</span>
                            <span style="color:#9CA3AF;">({int(rating)}/5)</span>
                        </div>
                        {f'<div style="color:#E5E7EB; font-size:14px; margin-top:5px; white-space:pre-wrap;">{comments}</div>' if comments.strip() else '<div style="color:#9CA3AF; font-size:13px; font-style:italic;">No additional comments</div>'}
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Feedback form for services without feedback
                with st.form(key=f"feedback_form_{idx}_{vehicle_id}"):
                    st.markdown("### 💬 Rate Your Service Experience")
                    rating = st.slider(
                        "Rating",
                        min_value=1,
                        max_value=5,
                        value=5,
                        key=f"rating_{idx}_{vehicle_id}",
                        help="Rate your service experience from 1 (Poor) to 5 (Excellent)"
                    )
                    
                    # Show stars preview
                    stars_display = '⭐' * rating
                    st.markdown(f"""
                        <div style="text-align:center; padding:10px; background:rgba(250, 204, 21, 0.1); 
                                   border-radius:8px; margin:10px 0;">
                            <span style="font-size:24px; color:#FACC15;">{stars_display}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    comment = st.text_area(
                        "Comments (Optional)",
                        key=f"comment_{idx}_{vehicle_id}",
                        placeholder="Tell us about your service experience...",
                        height=100
                    )
                    
                    submitted = st.form_submit_button("💾 Submit Feedback", type="primary")
                    
                    if submitted:
                        try:
                            fb.collect_feedback(vehicle_id, rating, comment)
                            reload_feedback_db()  # Reload after saving
                            st.success("✅ Thank you for your feedback!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error submitting feedback: {e}")
            
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing between services
    else:
        st.info("No service history found.")

elif selection == "Profile":
    st.header("Vehicle Profile")
    st.markdown("""
    <div class="customer-card">
        <div style="text-align:center; padding:20px;">
            <div style="font-size:60px; margin-bottom:10px;">🚘</div>
            <h2 style="color:white; margin:0;">Tesla Model 3</h2>
            <p style="color:#9CA3AF;">VIN: 5YJ3E1EA1JF8392</p>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px;">
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; text-align:center;">
                <div style="font-size:12px; color:#9CA3AF;">Mileage</div>
                <div style="font-weight:700; color:white;">42,391 mi</div>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; text-align:center;">
                <div style="font-size:12px; color:#9CA3AF;">Software</div>
                <div style="font-weight:700; color:white;">v11.1</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
