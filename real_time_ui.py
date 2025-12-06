"""
Real-time UI to show DataAnalysisAgent analysis results (computed features)
from the rolling 10-reading context window.

Run:
    streamlit run real_time_ui.py
"""

import time
import streamlit as st
import pandas as pd
from datetime import datetime

from data_analysis_agent import DataAnalysisAgent, WINDOW_SIZE, POLL_INTERVAL
from customer_engagement_agent import CustomerEngagementAgent

VEHICLES = [f"VH{i:03d}" for i in range(1, 11)]

MAINTENANCE_HISTORY = {
    "VH001": {
        "last_service_km": 45000,
        "last_service_days_ago": 60,
        "num_repairs": 3,
        "last_failure_km": 42000,
    },
}


def ensure_state():
    """Initialize Streamlit session state."""
    if "agent" not in st.session_state:
        st.session_state.agent = DataAnalysisAgent(maintenance_history=MAINTENANCE_HISTORY)
    if "engagement_agent" not in st.session_state:
        st.session_state.engagement_agent = CustomerEngagementAgent()
    if "last_features" not in st.session_state:
        st.session_state.last_features = None
    if "last_fetch_times" not in st.session_state:
        st.session_state.last_fetch_times = {}
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []  # Store all analysis results over time
    if "chat_initialized" not in st.session_state:
        st.session_state.chat_initialized = {}  # Track if chat was started per vehicle


def ui_diagnosis_callback(features: dict):
    """Store latest analysis result for UI."""
    features_copy = dict(features)
    features_copy["analysis_timestamp"] = datetime.utcnow().isoformat()
    st.session_state.last_features = features_copy
    st.session_state.analysis_history.append(features_copy)


def main():
    st.set_page_config(page_title="Real-Time Telematics UI", page_icon="🚗", layout="wide")

    ensure_state()
    agent: DataAnalysisAgent = st.session_state.agent

    st.title("🚗 Real-Time Telematics Analysis Dashboard")
    st.markdown(
        f"**DataAnalysisAgent** analyzes telematics data every **{POLL_INTERVAL} sec** "
        f"using a rolling window of **{WINDOW_SIZE} readings**. Shows computed features, "
        "early warnings, and maintenance recommendations."
    )
    st.info("💡 **Tip:** The page auto-fetches when you interact with it. Use 'Fetch New Reading Now' for immediate updates.")

    st.sidebar.header("Settings")
    vehicle_id = st.sidebar.selectbox("Vehicle", VEHICLES, index=0)
    
    # Create tabs for Analysis and Customer Engagement
    tab1, tab2 = st.tabs(["📊 Analysis Dashboard", "💬 Customer Engagement Chatbot"])

    # Check timing for automatic fetch
    now = time.time()
    last_times = st.session_state.last_fetch_times
    last_ts = last_times.get(vehicle_id, 0)
    elapsed = now - last_ts

    # Manual refresh button (always available)
    if st.sidebar.button("🔄 Fetch New Reading Now"):
        agent.run_once(vehicle_id, ui_diagnosis_callback)
        last_times[vehicle_id] = time.time()
        st.rerun()

    # Auto-fetch if enough time has passed (on any rerun)
    if elapsed >= POLL_INTERVAL:
        agent.run_once(vehicle_id, ui_diagnosis_callback)
        last_times[vehicle_id] = now
        st.rerun()  # Rerun to show the new data immediately

    # Show status
    if elapsed < POLL_INTERVAL:
        remaining = POLL_INTERVAL - elapsed
        st.sidebar.info(f"⏱️ Next auto-fetch in: {remaining:.1f}s\n\nClick 'Fetch New Reading Now' to update immediately.")
    else:
        st.sidebar.success("✅ Ready to fetch!")

    window = list(agent.windows.get(vehicle_id, []))
    current_len = len(window)
    last_features = st.session_state.last_features
    engagement_agent = st.session_state.engagement_agent

    # ========================================================================
    # TAB 1: ANALYSIS DASHBOARD
    # ========================================================================
    with tab1:
        # Show progress toward analysis window
        if current_len < WINDOW_SIZE:
        st.warning(
            f"⏳ **Building analysis window:** Collected **{current_len}** of **{WINDOW_SIZE}** readings. "
            f"Analysis results will appear once the window is full."
        )
        st.progress(current_len / WINDOW_SIZE)
        
        # Show latest reading while building
        if current_len > 0:
            with st.expander("📡 Latest Raw Reading (preview)", expanded=False):
                st.json(window[-1])
            return

        # Window is full - show analysis results
        if last_features is None:
            st.info("Window is full but analysis not yet computed. Click 'Fetch New Reading Now' to trigger analysis.")
            return

        # ========================================================================
        # ANALYSIS RESULTS DISPLAY
        # ========================================================================
    
    st.success(f"✅ **Analysis Complete** - Window: {WINDOW_SIZE}/{WINDOW_SIZE} readings")

    # Key metrics row
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vehicle", last_features["vehicle_id"])
    with col2:
        st.metric("Engine Temp (°C)", f"{last_features['engine_temp']:.1f}")
    with col3:
        st.metric("Battery Voltage (V)", f"{last_features['battery_voltage']:.2f}")
    with col4:
        st.metric("KM Since Service", f"{last_features['km_since_service']:.0f}")

    # Early warning detection
    st.subheader("⚠️ Early Warning Status")
    high_engine_temp = last_features["engine_temp"] > 105 or last_features["engine_temp_avg"] > 100
    low_battery = last_features["battery_voltage"] < 11.5 or last_features["battery_avg"] < 11.7
    high_vibration = last_features["vibration_std"] > 0.6
    long_since_service = (
        last_features["km_since_service"] > 10000 or last_features["last_service_days_ago"] > 180
    )

    if (
        last_features["anomaly_flag"]
        or last_features["dtc_flag"]
        or high_engine_temp
        or low_battery
        or high_vibration
        or long_since_service
    ):
        st.error(
            "🚨 **EARLY WARNING DETECTED** - Vehicle should be **prioritized for maintenance scheduling**."
        )
        
        # Show specific issues
        issues = []
        if last_features["anomaly_flag"]:
            issues.append("Anomaly flag triggered")
        if last_features["dtc_flag"]:
            issues.append(f"DTC code: {last_features['dtc_code']}")
        if high_engine_temp:
            issues.append(f"High engine temp: {last_features['engine_temp']:.1f}°C")
        if low_battery:
            issues.append(f"Low battery: {last_features['battery_voltage']:.2f}V")
        if high_vibration:
            issues.append(f"High vibration std: {last_features['vibration_std']:.2f}")
        if long_since_service:
            issues.append(f"Long since service: {last_features['km_since_service']:.0f} km")
        
        st.write("**Issues detected:**")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ **No critical warnings** - Vehicle operating normally.")

    # Rolling statistics
    st.subheader("📈 Rolling Statistics (from 10-reading window)")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Engine Temp Avg", f"{last_features['engine_temp_avg']:.1f}°C")
        st.metric("Engine Temp Std", f"{last_features['engine_temp_std']:.2f}")
    with col_s2:
        st.metric("Battery Avg", f"{last_features['battery_avg']:.2f}V")
        st.metric("Battery Drop", f"{last_features['battery_drop']:.3f}V")
    with col_s3:
        st.metric("Temp Rise Rate", f"{last_features['temp_rise_rate']:.2f}°C")
        st.metric("Coolant Rise Rate", f"{last_features['coolant_rise_rate']:.2f}°C")
    with col_s4:
        st.metric("Vibration Std", f"{last_features['vibration_std']:.3f}")
        st.metric("Mileage", f"{last_features['mileage']:,} km")

    # Maintenance context
    st.subheader("🔧 Maintenance Context")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Last Service KM", f"{last_features['last_service_km']:,}")
    with col_m2:
        st.metric("Days Since Service", f"{last_features['last_service_days_ago']:.0f}")
    with col_m3:
        st.metric("Number of Repairs", f"{int(last_features['num_repairs'])}")
    with col_m4:
        st.metric("KM Since Failure", f"{last_features['km_since_failure']:.0f}")

    # Trend visualization (if we have history)
    if len(st.session_state.analysis_history) > 1:
        st.subheader("📉 Analysis Trends Over Time")
        hist_df = pd.DataFrame(st.session_state.analysis_history)
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.line_chart(
                hist_df.set_index("analysis_timestamp")[["engine_temp", "engine_temp_avg"]],
                use_container_width=True,
            )
        with col_t2:
            st.line_chart(
                hist_df.set_index("analysis_timestamp")[["battery_voltage", "battery_avg"]],
                use_container_width=True,
            )

    # Raw features (collapsible)
    with st.expander("🔍 Full Computed Features (JSON)", expanded=False):
        st.json(last_features)

        # Context window (collapsible)
        with st.expander(f"📋 Raw Context Window ({WINDOW_SIZE} readings)", expanded=False):
            df_window = pd.DataFrame(window)
            st.dataframe(df_window, use_container_width=True)

    # ========================================================================
    # TAB 2: CUSTOMER ENGAGEMENT CHATBOT
    # ========================================================================
    with tab2:
        st.subheader("💬 Personalized Vehicle Health Chatbot")
        st.markdown(
            "Get personalized explanations about your vehicle's health status and "
            "recommended service actions in a conversational format."
        )

        # Check if we have analysis results
        if last_features is None or current_len < WINDOW_SIZE:
            st.warning(
                f"⏳ Please wait for the analysis window to complete ({current_len}/{WINDOW_SIZE} readings). "
                "The chatbot will be available once analysis is ready."
            )
        else:
            # Initialize conversation if not already started
            if vehicle_id not in st.session_state.chat_initialized:
                greeting_message = engagement_agent.generate_conversation_message(
                    last_features, greeting=True
                )
                engagement_agent.add_to_conversation(vehicle_id, greeting_message, "assistant")
                st.session_state.chat_initialized[vehicle_id] = True

            # Display conversation history
            conversation = engagement_agent.get_conversation_history(vehicle_id)
            
            # Chat container
            chat_container = st.container()
            with chat_container:
                for msg in conversation:
                    if msg["role"] == "assistant":
                        with st.chat_message("assistant"):
                            st.markdown(msg["content"])
                    else:
                        with st.chat_message("user"):
                            st.markdown(msg["content"])

            # Generate new message if analysis has updated
            if last_features and len(conversation) > 0:
                # Check if this is a new analysis (compare timestamps)
                latest_analysis_time = last_features.get("analysis_timestamp", "")
                last_msg_time = conversation[-1].get("timestamp", "")
                
                if latest_analysis_time > last_msg_time:
                    # New analysis available - generate update message
                    update_message = engagement_agent.generate_conversation_message(
                        last_features, greeting=False
                    )
                    engagement_agent.add_to_conversation(vehicle_id, update_message, "assistant")
                    st.rerun()

            # User input
            user_input = st.chat_input("Ask about your vehicle's health or service recommendations...")
            
            if user_input:
                # Add user message
                engagement_agent.add_to_conversation(vehicle_id, user_input, "user")
                
                # Generate response based on user query and current analysis
                if last_features:
                    # Simple response logic (can be enhanced with LLM)
                    response = engagement_agent._generate_response_to_query(
                        user_input, last_features
                    )
                else:
                    response = "I'm still analyzing your vehicle data. Please wait for the analysis to complete."
                
                engagement_agent.add_to_conversation(vehicle_id, response, "assistant")
                st.rerun()

            # Action buttons
            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🔄 Refresh Analysis Message"):
                    if last_features:
                        update_message = engagement_agent.generate_conversation_message(
                            last_features, greeting=False
                        )
                        engagement_agent.add_to_conversation(vehicle_id, update_message, "assistant")
                        st.rerun()
            
            with col_btn2:
                if st.button("📋 Show Service Recommendations"):
                    if last_features:
                        issues = engagement_agent.analyze_issues(last_features)
                        recommendation = engagement_agent.generate_recommendation(issues, last_features)
                        
                        rec_message = f"""
**Service Recommendations for {recommendation['vehicle_id']}**

**Priority:** {recommendation['priority'].upper()}
**Urgency:** {recommendation['urgency']}
**Estimated Cost:** {recommendation['estimated_cost_range']}

**Recommended Actions:**
"""
                        for i, action in enumerate(recommendation['recommended_actions'], 1):
                            rec_message += f"{i}. {action}\n"
                        
                        rec_message += f"\n**Next Service Due:** ~{recommendation['next_service_km']:,} km"
                        
                        engagement_agent.add_to_conversation(vehicle_id, rec_message, "assistant")
                        st.rerun()
            
            with col_btn3:
                if st.button("🗑️ Clear Chat History"):
                    if vehicle_id in engagement_agent.conversation_history:
                        engagement_agent.conversation_history[vehicle_id] = []
                    st.session_state.chat_initialized[vehicle_id] = False
                    st.rerun()


if __name__ == "__main__":
    main()
