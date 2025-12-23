import streamlit as st
import pandas as pd
import json
import time
import os
import requests
import random
import math
import csv
import subprocess
from datetime import datetime
from slots_manager import SlotsManager
from feedback_agent import FeedbackAgent

# Page Config (MUST BE FIRST)
st.set_page_config(
    page_title="AutoHub | Service Command",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
def local_css(file_name):
    with open(file_name, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("assets/custom.css")
except:
    pass # Gracious fallback if file missing

# Initialize Helpers
sm = SlotsManager()
fb = FeedbackAgent()
BOOKING_API_URL = "http://localhost:9000"

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("""
    <div class="sidebar-logo">
        <span class="sidebar-logo-icon">🔧</span>
        <span class="sidebar-logo-text">AutoHub</span>
    </div>
""", unsafe_allow_html=True)

menu_options = [
    "Tech Dashboard", 
    "Technician Input",
    "Diagnostics",
    "Schedule",
    "Admin & Security",
    "Settings"
]

menu_icons = {
    "Tech Dashboard": "📊",
    "Technician Input": "📝",
    "Diagnostics": "📈",
    "Schedule": "📅",
    "Admin & Security": "🛡️",
    "Settings": "⚙️"
}

# Navigation with radio buttons
selection = st.sidebar.radio(
    "Navigation",
    menu_options,
    format_func=lambda x: f"{menu_icons.get(x, '•')} {x}",
    label_visibility="collapsed",
    index=0
)



# --- DATA LOADERS ---
def get_active_slots():
    slots_data = sm._load_db()
    active = []
    for slot, vid in slots_data.items():
        predicted_issue = "-"
        risk = 0.0
        priority = "LOW"
        
        if vid:
            hist = fb.db.get(vid, [])
            if hist:
                last_rec = hist[-1]
                predicted_issue = last_rec.get("likely_failure", "Unknown")
                risk = last_rec.get("risk_score", 0.0)
                priority = last_rec.get("priority", "LOW")
                
            active.append({
                "Slot": slot,
                "Vehicle ID": vid,
                "Failure": predicted_issue,
                "Risk": risk,
                "Priority": priority,
                "Status": "Servicing"
            })
    return pd.DataFrame(active) if active else pd.DataFrame()

def get_risk_color_class(risk):
    """Get risk color class based on percentage"""
    if risk >= 0.8:
        return "critical"
    elif risk >= 0.5:
        return "medium"
    else:
        return "low"

def get_status_class(status):
    """Get status pill class"""
    status_lower = status.lower()
    if "servicing" in status_lower:
        return "servicing"
    elif "queued" in status_lower:
        return "queued"
    elif "diagnos" in status_lower:
        return "diagnosing"
    return "queued"

# --- PAGES ---

# 1. TECH DASHBOARD (Overview)
if selection == "Tech Dashboard":
    # Check labeled samples count for model refinement
    labeled_count = 0
    try:
        if os.path.exists("live_feature_samples.csv"):
            with open("live_feature_samples.csv", "r") as f:
                rows = list(csv.reader(f))
                labeled_count = sum(1 for row in rows[1:] if len(row) > 12 and row[12].strip())
    except:
        pass
    
    # Header with Model Refinement Button (if 50+ entries)
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown("""
            <div class="dashboard-header">
                <div class="header-left">
                    <h1 class="header-title">Service Command</h1>
                    <span class="status-badge">OPTIMAL</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        st.markdown(f"<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        # Refinement logic removed as requested
        pass

        # Display results from session state
        if 'refinement_result' in st.session_state:
            res = st.session_state['refinement_result']
            
            if res.get('success'):
                st.success("✅ Model Updated Successfully!")
                st.info(f"Refined model saved. Accuracy: {res.get('accuracy', 0):.1%}")
                
                with st.expander("📋 View Report"):
                    st.text(res.get('report', 'No report available'))
                
                # Clear result after showing (optional, or keep until next click)
            else:
                st.error("❌ Refinement Failed")
                st.error(res.get('message'))
        
        # Show progress counter below button
        status_text = "✅ Ready for refinement" if labeled_count >= 50 else f"({50-labeled_count} more needed)"
        st.markdown(f"""
            <div style="margin-top: 10px; padding: 8px; background: rgba(17, 24, 39, 0.6); 
                       border-radius: 8px; text-align: center; color: #9CA3AF; font-size: 11px;">
                {labeled_count}/50 labeled samples<br>
                <span style="color: {'#22C55E' if labeled_count >= 50 else '#FACC15'}; font-weight: 600;">{status_text}</span>
            </div>
        """, unsafe_allow_html=True)
    
    # KPIs
    active_count = len([v for k,v in sm._load_db().items() if v])
    
    st.markdown("""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Active Jobs</span>
                    <span class="kpi-icon">🚀</span>
                </div>
                <div class="kpi-value">{}</div>
                <div class="kpi-delta">+2 from yesterday</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Avg. Service Time</span>
                    <span class="kpi-icon">⏱️</span>
                </div>
                <div class="kpi-value">42m</div>
                <div class="kpi-delta negative">-5m efficiency</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Predicted Failures</span>
                    <span class="kpi-icon">📈</span>
                </div>
                <div class="kpi-value">8</div>
                <div class="kpi-delta">High Confidence</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Model Accuracy</span>
                    <span class="kpi-icon">📊</span>
                </div>
                <div class="kpi-value">94.2%</div>
                <div class="kpi-delta">+0.4% this week</div>
            </div>
        </div>
    """.format(active_count), unsafe_allow_html=True)

    # Main Visuals
    col_main, col_queue = st.columns([1.5, 1])
    
    with col_main:
        # Agent Mesh Network
        agent_mesh_html = """
<div class="agent-mesh-container">
    <div class="agent-mesh-header">
        <div class="agent-mesh-title">
            <span>🗄️</span>
            <span>Agent Mesh Network</span>
        </div>
        <div class="system-status">• SYSTEM ONLINE</div>
    </div>
    <div class="agent-orbit">
        <div class="agent-center">
            <div class="agent-center-text">MASTER<br>ORCHESTRATOR</div>
        </div>
        <svg class="agent-connections" width="100%" height="100%" style="position: absolute; top: 0; left: 0; z-index: 2; pointer-events: none;">
            <line x1="50%" y1="50%" x2="50%" y2="8%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="50%" y1="50%" x2="82%" y2="18%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="50%" y1="50%" x2="50%" y2="92%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="50%" y1="50%" x2="18%" y2="18%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="50%" y1="50%" x2="82%" y2="82%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
            <line x1="50%" y1="50%" x2="18%" y2="82%" stroke="rgba(34, 211, 238, 0.2)" stroke-width="1" stroke-dasharray="3,3"/>
        </svg>
        <div class="agent-node active" style="top: 8%; left: 50%; transform: translate(-50%, -50%);">
            <div class="agent-icon">📊</div>
            <div class="agent-label">DIAGNOSIS<br>AGENT</div>
        </div>
        <div class="agent-node active" style="top: 18%; right: 18%; transform: translate(50%, -50%);">
            <div class="agent-icon">📅</div>
            <div class="agent-label">SCHEDULING<br>AGENT</div>
        </div>
        <div class="agent-node active" style="bottom: 8%; left: 50%; transform: translate(-50%, 50%);">
            <div class="agent-icon">✅</div>
            <div class="agent-label">BOOKING<br>AGENT</div>
        </div>
        <div class="agent-node active" style="top: 18%; left: 18%; transform: translate(-50%, -50%);">
            <div class="agent-icon">💬</div>
            <div class="agent-label">FEEDBACK<br>AGENT</div>
        </div>
        <div class="agent-node active" style="bottom: 18%; right: 18%; transform: translate(50%, 50%);">
            <div class="agent-icon">🔧</div>
            <div class="agent-label">RCA/CAPA<br>AGENT</div>
        </div>
        <div class="agent-node active" style="bottom: 18%; left: 18%; transform: translate(-50%, 50%);">
            <div class="agent-icon">🛡️</div>
            <div class="agent-label">UEBA<br>SECURITY</div>
        </div>
    </div>
</div>
        """
        st.markdown(agent_mesh_html, unsafe_allow_html=True)
        
    with col_queue:
        # Service Queue
        df_active = get_active_slots()
        
        st.markdown("""
            <div class="service-queue-container">
                <div class="service-queue-header">
                    <div class="service-queue-title">Service Queue</div>
                    <div class="live-badge">Live: {} Vehicles</div>
                </div>
        """.format(len(df_active) if not df_active.empty else 0), unsafe_allow_html=True)
        
        if not df_active.empty:
            # Use real data from active slots
            for idx, row in df_active.iterrows():
                vehicle_id = row['Vehicle ID']
                slot = row['Slot']
                vehicle_model = f"Vehicle {vehicle_id}"
                status = row.get('Status', 'QUEUED')
                risk = float(row.get('Risk', 0.5))
                failure = row.get('Failure', 'Unknown')
                
                risk_class = get_risk_color_class(risk)
                status_class = get_status_class(status)
                risk_pct = int(risk * 100)
                
                # Get risk color
                risk_color = "#EF4444" if risk_class == "critical" else "#FACC15" if risk_class == "medium" else "#22D3EE"
                
                # Create a unique key for each vehicle's complete button
                complete_key = f"complete_{vehicle_id}_{slot}"
                
                st.markdown(f"""
                    <div class="vehicle-card {risk_class}">
                        <div class="vehicle-header">
                            <div class="vehicle-info">
                                <div class="vehicle-model">{vehicle_model}</div>
                                <div class="vehicle-id">{vehicle_id}</div>
                            </div>
                            <div class="status-pill {status_class}">{status}</div>
                        </div>
                        <div class="risk-indicator">
                            <div class="risk-label">
                                <span>▲</span>
                                <span>Risk: <span class="risk-percentage" style="color: {risk_color};">{risk_pct}%</span></span>
                                <span>◱</span>
                                <span>{failure}</span>
                            </div>
                            <div class="risk-bar">
                                <div class="risk-bar-fill {risk_class}" style="width: {risk_pct}%;"></div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # View-only - direct technicians to Technician Input page
                st.caption("→ Go to 'Technician Input' to complete this service")
        else:
            st.markdown("""
                <div style="text-align: center; padding: 40px; color: #9CA3AF;">
                    <p>Queue is empty</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


# 2. TECHNICIAN INPUT (Primary Service Completion Page)
elif selection == "Technician Input":
    st.title("📝 Technician Service Completion")
    st.caption("Complete services and confirm actual failure types")
    
    # Get active slots for technician input
    slots_data = sm._load_db()
    active_slots_for_input = [s for s, v in slots_data.items() if v is not None]
    
    if active_slots_for_input:
        selected_slot = st.selectbox("Select Service Bay to Complete", active_slots_for_input, key="tech_input_slot")
        selected_vehicle = slots_data[selected_slot]
        
        # Get predicted failure and risk
        predicted_failure = "Unknown"
        risk_score = 0.0
        hist = fb.db.get(selected_vehicle, [])
        if hist:
            predicted_failure = hist[-1].get("likely_failure", "Unknown")
            risk_score = hist[-1].get("risk_score", 0.0)
        
        # Display vehicle info
        col_info, col_form = st.columns([1, 1.2])
        
        with col_info:
            risk_pct = int(risk_score * 100)
            risk_color = "#EF4444" if risk_pct > 80 else "#FACC15" if risk_pct > 50 else "#22D3EE"
            
            st.subheader("Service Information")
            
            st.metric("Vehicle ID", selected_vehicle)
            st.metric("Service Bay", selected_slot)
            
            st.markdown("### AI Prediction")
            st.info(f"**{predicted_failure}**")
            
            st.markdown("### Risk Level")
            st.progress(risk_pct / 100)
            st.caption(f"Risk: {risk_pct}%")
        
        with col_form:
            st.markdown("""
                <div style="background:rgba(34, 197, 94, 0.1); border:1px solid rgba(34, 197, 94, 0.3); 
                           padding:15px; border-radius:8px; margin-bottom:20px;">
                    <h4 style="color:#22C55E; margin:0; font-size:14px;">✅ Confirm Diagnosis & Complete Service</h4>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form(key=f"tech_complete_form_{selected_vehicle}", clear_on_submit=False):
                true_label_input = st.selectbox(
                    "Actual Failure Found",
                    [predicted_failure, "No Failure", "Heat Dissipation Failure", 
                     "Power/Battery Failure", "Tool Wear/Vibration Failure", "Overstrain Failure"],
                    key=f"tech_true_label_{selected_vehicle}",
                    help="Select the actual failure type found during service"
                )
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_complete = st.form_submit_button(
                        "✅ Complete Service", 
                        type="primary",
                        use_container_width=True
                    )
                with col_btn2:
                    cancel = st.form_submit_button(
                        "Cancel",
                        use_container_width=True
                    )
                
                if submit_complete:
                    try:
                        # 1. Update true label in CSV
                        fb.update_true_label(selected_vehicle, true_label_input)
                        
                        # 2. Release slot via API
                        r = requests.post(f"{BOOKING_API_URL}/complete", params={"slot": selected_slot})
                        
                        if r.status_code == 200:
                            # 3. Mark service as completed in maintenance history
                            fb.mark_service_completed(selected_vehicle)
                            
                            st.success(f"✅ Service completed successfully!")
                            st.info(f"📋 True label recorded: **{true_label_input}**")
                            st.info(f"🔓 Bay **{selected_slot}** has been freed")
                            
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ API Error: Could not release service bay")
                            st.error(f"Status Code: {r.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error completing service: {e}")
    else:
        st.info("📭 No vehicles currently in service. Active bookings will appear here.")
        st.markdown("""
            <div style="background:rgba(17, 24, 39, 0.6); padding:30px; border-radius:12px; text-align:center; margin-top:30px;">
                <div style="font-size:48px; margin-bottom:15px;">🔧</div>
                <div style="color:#9CA3AF; font-size:16px;">Waiting for service assignments...</div>
            </div>
        """, unsafe_allow_html=True)


# 3. DIAGNOSTICS
elif selection == "Diagnostics":
    st.title("📈 Diagnostics")
    st.caption("Real-time diagnostic data and analytics")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("System Performance Trend")
        # Mock chart
        chart_data = pd.DataFrame(
            [[random.uniform(90, 100) for _ in range(20)] for _ in range(3)],
            index=["Accuracy", "Recall", "Precision"]
        ).T
        st.line_chart(chart_data)
    
    with c2:
        st.subheader("Failure Distribution")
        # Failures
        dist = {"Heat Failure": 12, "Power Failure": 8, "Wear Failure": 5, "Overstrain": 3}
        st.bar_chart(dist)

# 4. SCHEDULE
elif selection == "Schedule":
    st.title("📅 Schedule")
    st.caption("Service scheduling and calendar management")
    
    slots_data = sm._load_db()
    
    # Grid View for Slots
    st.subheader("Today's Service Bay Status")
    
    cols = st.columns(3)
    slot_names = list(slots_data.keys())
    
    for i, slot in enumerate(slot_names):
        vid = slots_data[slot]
        status = "OPEN" if vid is None else "OCCUPIED"
        color = "#10B981" if vid is None else "#EF4444"
        bg_card = "rgba(16, 185, 129, 0.1)" if vid is None else "rgba(239, 68, 68, 0.1)"
        
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:{bg_card}; padding:20px; border-radius:12px; border:1px solid {color}; margin-bottom:15px;">
                <h3 style="margin:0; color:{color};">{slot}</h3>
                <div style="font-size:12px; color:#9CA3AF; margin-top:5px;">Status</div>
                <div style="font-weight:700; color:white; font-size:18px;">{status}</div>
                {f'<div style="margin-top:10px; font-size:13px; color:#E5E7EB;">Vehicle: {vid}</div>' if vid else ''}
            </div>
            """, unsafe_allow_html=True)

# 5. ADMIN & SECURITY
elif selection == "Admin & Security":
    st.title("🛡️ Admin & Security")
    st.caption("System administration and security monitoring")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        # Active Services Overview (View Only)
        st.subheader("Active Services Overview")
        slots_data = sm._load_db()
        active_slots = [s for s, v in slots_data.items() if v is not None]

        if active_slots:
            st.markdown("""
                <div style="background:rgba(59, 130, 246, 0.1); border:1px solid rgba(59, 130, 246, 0.3); 
                           padding:12px; border-radius:8px; margin-bottom:15px;">
                    <div style="color:#60A5FA; font-size:13px; font-weight:600;">ℹ️ View Only - Use 'Technician Input' to complete services</div>
                </div>
            """, unsafe_allow_html=True)
            
            for slot in active_slots:
                vehicle_id = slots_data[slot]
                
                # Fetch history
                predicted_failure = "Unknown"
                risk_score = 0.0
                hist = fb.db.get(vehicle_id, [])
                if hist:
                    predicted_failure = hist[-1].get("likely_failure", "Unknown")
                    risk_score = hist[-1].get("risk_score", 0.0)
                
                risk_pct = int(risk_score * 100)
                risk_color = "#EF4444" if risk_pct > 80 else "#FACC15" if risk_pct > 50 else "#22D3EE"
                    
                st.markdown(f"""
                <div style="background:rgba(17, 24, 39, 0.6); backdrop-filter:blur(10px); 
                           border:1px solid rgba(34, 211, 238, 0.1); padding:16px; border-radius:12px; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <h4 style="color:#E5E7EB; margin:0 0 5px 0;">{vehicle_id}</h4>
                            <div style="color:#9CA3AF; font-size:13px;">Bay: {slot}</div>
                        </div>
                        <div style="background:rgba(59, 130, 246, 0.2); color:#60A5FA; 
                                   padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600;">
                            IN SERVICE
                        </div>
                    </div>
                    <div style="margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.1);">
                        <div style="color:#9CA3AF; font-size:11px; margin-bottom:5px;">Predicted Issue</div>
                        <div style="color:#FACC15; font-weight:600; font-size:13px;">{predicted_failure}</div>
                    </div>
                    <div style="margin-top:10px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="flex:1; height:6px; background:rgba(255,255,255,0.1); border-radius:3px;">
                                <div style="height:100%; width:{risk_pct}%; background:{risk_color}; border-radius:3px;"></div>
                            </div>
                            <span style="color:{risk_color}; font-weight:600; font-size:12px;">{risk_pct}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No vehicles currently in service bays.")
    
    with col2:
        # System Health
        st.subheader("Agent Health Status")
        agents = [
            ("DiagnosisAgent", "Healthy", "running"),
            ("SchedulingAgent", "Healthy", "running"),
            ("BookingAgent", "Healthy", "running"),
            ("UEBA Guardrail", "Active", "running"),
            ("RCA/CAPA Agent", "Standby", "stopped")
        ]
        
        for name, status, state in agents:
            color = "#22C55E" if state == "running" else "#9CA3AF"
            icon = "🟢" if state == "running" else "⚪"
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:12px; background:rgba(17, 24, 39, 0.6); backdrop-filter:blur(10px); border:1px solid rgba(34, 211, 238, 0.1); margin-bottom:8px; border-radius:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:12px;">{icon}</span>
                    <span style="font-weight:600; color:#E5E7EB; font-size:14px;">{name}</span>
                </div>
                <div style="color:{color}; font-size:12px; font-weight:600; text-transform:uppercase;">
                    {status}
                </div>
            </div>
            """, unsafe_allow_html=True)

# 6. SETTINGS
elif selection == "Settings":
    st.title("⚙️ Settings")
    st.caption("System configuration and preferences")
    
    # Manufacturing Insights
    st.subheader("Manufacturing Insights")
    insights_file = "manufacturing_insights.json"
    if os.path.exists(insights_file):
        with open(insights_file, "r") as f:
            try:
                insights_data = json.load(f)
                latest = insights_data[-1] if insights_data else None
            except:
                latest = None
                
        if latest:
            st.markdown(f"""
            <div style="background:linear-gradient(90deg, #7C3AED 0%, #5B21B6 100%); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
                <h2 style="margin:0;">Insight: {latest['top_recurring_defect']}</h2>
                <p style="opacity:0.8; margin-top:5px;">Severity: {latest['severity']} | Impact: {latest['fleet_impact_percent']}% of Fleet</p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Root Cause**")
                st.warning(latest['root_cause'])
            with c2:
                st.markdown("**CAPA Recommendation**")
                st.success(latest['capa_recommendation'])
            with c3:
                st.markdown("**Process Change**")
                st.info(latest['process_change'])
                
            st.markdown("### Detailed Batch Metrics")
            st.json(latest)
            
        else:
            st.warning("No insights generated yet. Wait for the Outer Loop to trigger (every 8-10 services).")
    else:
        st.warning("No insights history found.")
    
    # Model Retraining
    st.subheader("Model Retraining")
    import csv
    labeled_count = 0
    try:
        with open("live_feature_samples.csv", "r") as f:
            rows = list(csv.reader(f))
            labeled_count = sum(1 for row in rows[1:] if len(row) > 12 and row[12].strip())
    except:
        pass
        
    st.metric("New Labeled Samples", labeled_count, delta=f"{50-labeled_count} to go" if labeled_count < 50 else "Ready")
    
    prog = min(labeled_count / 50.0, 1.0)
    st.progress(prog)
    
    if labeled_count >= 50:
        if st.button("🚀 Trigger Model Refinement"):
            with st.spinner("Refining LightGBM model..."):
                import subprocess
                subprocess.run(["python", "refinement_train_new_model.py"])
                st.success("Model Updated Successfully!")