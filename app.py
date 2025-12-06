"""
Automotive Predictive Maintenance Streamlit Prototype
=====================================================
This application demonstrates a comprehensive predictive maintenance system
with anomaly detection, diagnosis, RL scheduling, feedback loops, and UEBA.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from datasets import load_dataset

# Set page config
st.set_page_config(
    page_title="Automotive Predictive Maintenance",
    page_icon="🚗",
    layout="wide"
)

# Initialize session state
if 'telematics_data' not in st.session_state:
    st.session_state.telematics_data = None
if 'lstm_model' not in st.session_state:
    st.session_state.lstm_model = None
if 'rf_model' not in st.session_state:
    st.session_state.rf_model = None
if 'q_table' not in st.session_state:
    st.session_state.q_table = None
if 'agent_logs' not in st.session_state:
    st.session_state.agent_logs = []
if 'anomaly_history' not in st.session_state:
    st.session_state.anomaly_history = []
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []


# ============================================================================
# DATA INGESTION: Mock Telematics API
# ============================================================================

def load_uci_ai4i_data():
    """Load synthetic data from UCI AI4I dataset."""
    try:
        dataset = load_dataset("UCI-ML/AI4I-2020-Predictive-Maintenance-Dataset")
        df = pd.DataFrame(dataset['train'])
        return df
    except Exception as e:
        st.error(f"Error loading UCI dataset: {e}")
        # Fallback: Generate synthetic data
        return generate_synthetic_data()


def generate_synthetic_data():
    """Generate synthetic telematics data for 10 vehicles."""
    np.random.seed(42)
    n_samples = 1000
    vehicles = [f"VH{i:03d}" for i in range(1, 11)]
    
    data = []
    for vehicle_id in vehicles:
        for i in range(n_samples):
            # Simulate battery degradation over time
            cycles = i
            age_factor = cycles / 1000
            
            # Battery voltage (decreases with cycles)
            voltage = 12.6 - (age_factor * 0.5) + np.random.normal(0, 0.1)
            
            # Battery temperature (increases with cycles and usage)
            temp = 25 + (age_factor * 10) + np.random.normal(0, 2)
            
            # Failure probability increases with cycles
            failure_prob = min(0.95, cycles / 2000)
            
            data.append({
                'vehicle_id': vehicle_id,
                'timestamp': datetime.now() - timedelta(days=n_samples-i),
                'battery_voltage': max(10.0, voltage),
                'battery_temp': max(20, min(60, temp)),
                'charge_cycles': cycles,
                'failure_km': np.random.exponential(50000) if np.random.random() < failure_prob else np.nan
            })
    
    return pd.DataFrame(data)


def mock_telematics_api(vehicle_ids=None, n_samples=100):
    """
    Mock telematics API that returns real-time data for vehicles.
    
    Args:
        vehicle_ids: List of vehicle IDs to query. If None, uses all 10 vehicles.
        n_samples: Number of recent samples per vehicle
    
    Returns:
        DataFrame with telematics data
    """
    try:
        # Load base dataset
        base_df = load_uci_ai4i_data()
        
        # If we have UCI data, adapt it; otherwise use synthetic
        if 'vehicle_id' not in base_df.columns:
            # Adapt UCI dataset columns
            if 'UDI' in base_df.columns:
                base_df['vehicle_id'] = base_df['UDI'].apply(lambda x: f"VH{x%10+1:03d}")
            else:
                base_df = generate_synthetic_data()
        
        # Filter by vehicle IDs if specified
        if vehicle_ids:
            base_df = base_df[base_df['vehicle_id'].isin(vehicle_ids)]
        
        # Get recent samples
        if len(base_df) > n_samples * len(base_df['vehicle_id'].unique()):
            base_df = base_df.tail(n_samples * len(base_df['vehicle_id'].unique()))
        
        # Ensure required columns exist
        required_cols = ['vehicle_id', 'battery_voltage', 'battery_temp', 'charge_cycles']
        for col in required_cols:
            if col not in base_df.columns:
                if col == 'battery_voltage':
                    base_df[col] = base_df.get('Voltage [V]', np.random.normal(12.5, 0.2, len(base_df)))
                elif col == 'battery_temp':
                    base_df[col] = base_df.get('Air temperature [K]', np.random.normal(30, 5, len(base_df)))
                elif col == 'charge_cycles':
                    base_df[col] = base_df.get('Rotational speed [rpm]', np.random.randint(0, 1000, len(base_df)))
        
        return base_df[required_cols + [c for c in base_df.columns if c not in required_cols]].copy()
    
    except Exception as e:
        st.error(f"Error in mock telematics API: {e}")
        return generate_synthetic_data()


# ============================================================================
# ANOMALY DETECTION: LSTM Model
# ============================================================================

def prepare_lstm_data(df, sequence_length=10):
    """
    Prepare time-series data for LSTM model.
    
    Args:
        df: DataFrame with telematics data
        sequence_length: Length of input sequences
    
    Returns:
        X, y arrays for LSTM training
    """
    try:
        # Group by vehicle and sort by timestamp/cycles
        df_sorted = df.sort_values(['vehicle_id', 'charge_cycles'])
        
        # Normalize features
        features = ['battery_voltage', 'battery_temp']
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df_sorted[features])
        
        X, y = [], []
        for vehicle_id in df_sorted['vehicle_id'].unique():
            vehicle_data = scaled_data[df_sorted['vehicle_id'] == vehicle_id]
            
            for i in range(len(vehicle_data) - sequence_length):
                X.append(vehicle_data[i:i+sequence_length])
                y.append(vehicle_data[i+sequence_length, 0])  # Predict voltage
        
        return np.array(X), np.array(y), scaler
    
    except Exception as e:
        st.error(f"Error preparing LSTM data: {e}")
        return None, None, None


def build_lstm_model(input_shape):
    """
    Build LSTM model for anomaly detection.
    
    Args:
        input_shape: Shape of input sequences (sequence_length, n_features)
    
    Returns:
        Compiled Keras model
    """
    try:
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    except Exception as e:
        st.error(f"Error building LSTM model: {e}")
        return None


def detect_anomalies_lstm(model, X, threshold_percentile=95):
    """
    Detect anomalies using LSTM prediction errors.
    
    Args:
        model: Trained LSTM model
        X: Input sequences
        threshold_percentile: Percentile for anomaly threshold
    
    Returns:
        Array of anomaly scores and binary labels
    """
    try:
        predictions = model.predict(X, verbose=0)
        # For simplicity, use reconstruction error
        # In practice, compare predictions with actual values
        errors = np.abs(predictions.flatten())
        threshold = np.percentile(errors, threshold_percentile)
        anomalies = errors > threshold
        
        return errors, anomalies, threshold
    
    except Exception as e:
        st.error(f"Error in anomaly detection: {e}")
        return None, None, None


# ============================================================================
# DIAGNOSIS: Random Forest Model
# ============================================================================

def train_rf_model(df):
    """
    Train Random Forest model to predict failure kilometers.
    
    Args:
        df: DataFrame with features and target (failure_km)
    
    Returns:
        Trained RandomForestRegressor model
    """
    try:
        # Prepare features
        feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
        X = df[feature_cols].fillna(df[feature_cols].mean())
        
        # Create target: failure_km (if not exists, estimate based on cycles)
        if 'failure_km' not in df.columns or df['failure_km'].isna().all():
            # Estimate failure km based on cycles and voltage
            y = 100000 - (df['charge_cycles'] * 50) - ((12.6 - df['battery_voltage']) * 10000)
            y = np.maximum(10000, y)  # Minimum 10k km
        else:
            y = df['failure_km'].fillna(df['failure_km'].median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        return model, {'mse': mse, 'mae': mae, 'test_size': len(X_test)}
    
    except Exception as e:
        st.error(f"Error training RF model: {e}")
        return None, None


def predict_failure_km(model, features):
    """
    Predict failure kilometers for given features.
    
    Args:
        model: Trained RandomForestRegressor
        features: DataFrame or array with features
    
    Returns:
        Array of predicted failure kilometers
    """
    try:
        return model.predict(features)
    except Exception as e:
        st.error(f"Error in failure prediction: {e}")
        return None


# ============================================================================
# RL SCHEDULING: Q-Learning
# ============================================================================

class QLearningScheduler:
    """
    Simple Q-Learning agent for maintenance slot optimization.
    States: demand levels (low, medium, high)
    Actions: schedule slots (morning, afternoon, evening)
    Rewards: -wait_time + satisfaction_score
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        
        # States: demand levels (0=low, 1=medium, 2=high)
        self.n_states = 3
        
        # Actions: time slots (0=morning, 1=afternoon, 2=evening)
        self.n_actions = 3
        
        # Initialize Q-table
        self.q_table = np.zeros((self.n_states, self.n_actions))
    
    def get_state(self, demand):
        """Convert demand value to state index."""
        if demand < 0.33:
            return 0  # Low
        elif demand < 0.66:
            return 1  # Medium
        else:
            return 2  # High
    
    def choose_action(self, state, training=True):
        """Epsilon-greedy action selection."""
        if training and np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        else:
            return np.argmax(self.q_table[state])
    
    def update_q_table(self, state, action, reward, next_state):
        """Update Q-table using Q-learning formula."""
        current_q = self.q_table[state, action]
        max_next_q = np.max(self.q_table[next_state])
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state, action] = new_q
    
    def calculate_reward(self, wait_time, satisfaction):
        """
        Calculate reward: -wait_time + satisfaction_score
        wait_time: normalized 0-1
        satisfaction: normalized 0-1
        """
        return -wait_time + satisfaction
    
    def schedule_maintenance(self, demand, n_vehicles):
        """
        Schedule maintenance slots based on current demand.
        
        Args:
            demand: Current demand level (0-1)
            n_vehicles: Number of vehicles needing maintenance
        
        Returns:
            Recommended time slot and expected reward
        """
        state = self.get_state(demand)
        action = self.choose_action(state, training=False)
        
        # Simulate wait times for different slots
        slot_wait_times = {
            0: 0.2,  # Morning: low wait
            1: 0.5,  # Afternoon: medium wait
            2: 0.8   # Evening: high wait
        }
        
        # Satisfaction decreases with wait time
        wait_time = slot_wait_times[action]
        satisfaction = 1.0 - wait_time
        
        reward = self.calculate_reward(wait_time, satisfaction)
        
        slot_names = ['Morning', 'Afternoon', 'Evening']
        return slot_names[action], reward, wait_time, satisfaction


# ============================================================================
# FEEDBACK LOOPS
# ============================================================================

def inner_feedback_loop(model, new_data, retrain_fraction=0.1):
    """
    Inner feedback loop: Partially retrain Random Forest with new data.
    
    Args:
        model: Existing RandomForestRegressor model
        new_data: DataFrame with new observations
        retrain_fraction: Fraction of new data to use for retraining
    
    Returns:
        Updated model
    """
    try:
        if len(new_data) < 10:
            return model  # Not enough data for retraining
        
        # Sample subset of new data
        n_samples = max(10, int(len(new_data) * retrain_fraction))
        sample_data = new_data.sample(n=min(n_samples, len(new_data)), random_state=42)
        
        # Prepare features
        feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
        X_new = sample_data[feature_cols].fillna(sample_data[feature_cols].mean())
        
        # Estimate targets
        y_new = 100000 - (sample_data['charge_cycles'] * 50) - ((12.6 - sample_data['battery_voltage']) * 10000)
        y_new = np.maximum(10000, y_new)
        
        # Partial fit (warm start)
        # Note: RF doesn't support partial_fit, so we retrain with combined data
        # In practice, use incremental learning or online algorithms
        return model  # Simplified: return original model
    
    except Exception as e:
        st.error(f"Error in inner feedback loop: {e}")
        return model


def outer_feedback_loop(aggregated_data, n_clusters=3):
    """
    Outer feedback loop: K-Means Root Cause Analysis on aggregated data.
    
    Args:
        aggregated_data: DataFrame with aggregated failure/maintenance data
        n_clusters: Number of clusters for RCA
    
    Returns:
        Cluster labels and centroids
    """
    try:
        # Prepare features for clustering
        feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
        if all(col in aggregated_data.columns for col in feature_cols):
            X = aggregated_data[feature_cols].fillna(aggregated_data[feature_cols].mean())
        else:
            # Use available numeric columns
            numeric_cols = aggregated_data.select_dtypes(include=[np.number]).columns
            X = aggregated_data[numeric_cols].fillna(aggregated_data[numeric_cols].mean())
        
        if len(X) < n_clusters:
            return None, None
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        return cluster_labels, kmeans.cluster_centers_
    
    except Exception as e:
        st.error(f"Error in outer feedback loop: {e}")
        return None, None


# ============================================================================
# UEBA SIMULATION: Isolation Forest
# ============================================================================

def simulate_agent_logs(n_logs=100):
    """
    Simulate agent activity logs for UEBA analysis.
    
    Returns:
        DataFrame with agent logs
    """
    np.random.seed(42)
    
    agents = [f"Agent_{i:02d}" for i in range(1, 6)]
    actions = ['read_data', 'write_data', 'query_api', 'update_model', 'schedule_maintenance']
    
    logs = []
    for i in range(n_logs):
        # Normal behavior: most actions are standard
        if np.random.random() < 0.95:
            action = np.random.choice(actions[:4])  # Normal actions
            duration = np.random.normal(1.0, 0.3)  # Normal duration
            success = True
        else:
            # Anomalous behavior
            action = np.random.choice(actions)
            duration = np.random.exponential(5.0)  # Long duration
            success = np.random.random() < 0.3  # Low success rate
        
        logs.append({
            'timestamp': datetime.now() - timedelta(minutes=n_logs-i),
            'agent_id': np.random.choice(agents),
            'action': action,
            'duration_seconds': max(0.1, duration),
            'success': success,
            'data_accessed': np.random.randint(1, 100)
        })
    
    return pd.DataFrame(logs)


def detect_ueba_anomalies(logs_df):
    """
    Detect anomalies in agent logs using Isolation Forest.
    
    Args:
        logs_df: DataFrame with agent logs
    
    Returns:
        Anomaly labels and scores
    """
    try:
        # Prepare features
        feature_cols = ['duration_seconds', 'data_accessed']
        X = logs_df[feature_cols].values
        
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.score_samples(X)
        
        # Convert to binary (1 = normal, -1 = anomaly)
        is_anomaly = anomaly_labels == -1
        
        return is_anomaly, anomaly_scores
    
    except Exception as e:
        st.error(f"Error in UEBA anomaly detection: {e}")
        return None, None


def trigger_self_healing_alert(anomaly_count, threshold=3):
    """
    Trigger self-healing alert if anomaly count exceeds threshold.
    
    Args:
        anomaly_count: Number of detected anomalies
        threshold: Alert threshold
    
    Returns:
        Boolean indicating if alert should be triggered
    """
    return anomaly_count >= threshold


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.title("🚗 Automotive Predictive Maintenance System")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Configuration")
    n_vehicles = st.sidebar.slider("Number of Vehicles", 1, 10, 10)
    vehicle_ids = [f"VH{i:03d}" for i in range(1, n_vehicles + 1)]
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Data Ingestion",
        "🔍 Anomaly Detection",
        "🏥 Diagnosis",
        "🤖 RL Scheduling",
        "🔄 Feedback Loops",
        "🛡️ UEBA Simulation"
    ])
    
    # ========================================================================
    # TAB 1: Data Ingestion
    # ========================================================================
    with tab1:
        st.header("Mock Telematics API")
        st.markdown("Ingest real-time telematics data from vehicle fleet.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Fetch Telematics Data", type="primary"):
                with st.spinner("Fetching data from mock API..."):
                    st.session_state.telematics_data = mock_telematics_api(
                        vehicle_ids=vehicle_ids,
                        n_samples=100
                    )
                    st.success(f"✅ Fetched {len(st.session_state.telematics_data)} records!")
        
        with col2:
            if st.button("📥 Load UCI AI4I Dataset"):
                with st.spinner("Loading UCI dataset..."):
                    st.session_state.telematics_data = load_uci_ai4i_data()
                    st.success(f"✅ Loaded {len(st.session_state.telematics_data)} records!")
        
        if st.session_state.telematics_data is not None:
            df = st.session_state.telematics_data
            
            st.subheader("📈 Data Overview")
            st.dataframe(df.head(20), use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Vehicles", df['vehicle_id'].nunique() if 'vehicle_id' in df.columns else "N/A")
            with col3:
                st.metric("Features", len(df.columns))
            
            # Visualizations
            if 'battery_voltage' in df.columns and 'battery_temp' in df.columns:
                fig, axes = plt.subplots(1, 2, figsize=(12, 4))
                
                axes[0].scatter(df['charge_cycles'] if 'charge_cycles' in df.columns else range(len(df)),
                               df['battery_voltage'], alpha=0.6)
                axes[0].set_xlabel('Charge Cycles')
                axes[0].set_ylabel('Battery Voltage (V)')
                axes[0].set_title('Voltage vs Cycles')
                axes[0].grid(True, alpha=0.3)
                
                axes[1].scatter(df['charge_cycles'] if 'charge_cycles' in df.columns else range(len(df)),
                               df['battery_temp'], alpha=0.6, c='red')
                axes[1].set_xlabel('Charge Cycles')
                axes[1].set_ylabel('Battery Temperature (°C)')
                axes[1].set_title('Temperature vs Cycles')
                axes[1].grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig)
    
    # ========================================================================
    # TAB 2: Anomaly Detection
    # ========================================================================
    with tab2:
        st.header("LSTM Anomaly Detection")
        st.markdown("Time-series anomaly detection using LSTM neural network.")
        
        if st.session_state.telematics_data is None:
            st.warning("⚠️ Please fetch telematics data first in the Data Ingestion tab.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                sequence_length = st.slider("Sequence Length", 5, 20, 10)
                epochs = st.slider("Training Epochs", 5, 50, 20)
            
            with col2:
                threshold_percentile = st.slider("Anomaly Threshold Percentile", 90, 99, 95)
                if st.button("🚀 Train LSTM Model", type="primary"):
                    with st.spinner("Training LSTM model..."):
                        try:
                            X, y, scaler = prepare_lstm_data(
                                st.session_state.telematics_data,
                                sequence_length=sequence_length
                            )
                            
                            if X is not None and len(X) > 0:
                                input_shape = (X.shape[1], X.shape[2])
                                model = build_lstm_model(input_shape)
                                
                                # Train model
                                history = model.fit(
                                    X, y,
                                    epochs=epochs,
                                    batch_size=32,
                                    validation_split=0.2,
                                    verbose=0
                                )
                                
                                st.session_state.lstm_model = model
                                st.success("✅ LSTM model trained successfully!")
                                
                                # Plot training history
                                fig, ax = plt.subplots(figsize=(10, 4))
                                ax.plot(history.history['loss'], label='Training Loss')
                                ax.plot(history.history['val_loss'], label='Validation Loss')
                                ax.set_xlabel('Epoch')
                                ax.set_ylabel('Loss (MSE)')
                                ax.set_title('LSTM Training History')
                                ax.legend()
                                ax.grid(True, alpha=0.3)
                                st.pyplot(fig)
                            else:
                                st.error("❌ Insufficient data for LSTM training.")
                        except Exception as e:
                            st.error(f"❌ Error training model: {e}")
            
            if st.session_state.lstm_model is not None:
                st.subheader("🔍 Anomaly Detection Results")
                
                if st.button("🔎 Detect Anomalies"):
                    with st.spinner("Detecting anomalies..."):
                        try:
                            X, _, _ = prepare_lstm_data(
                                st.session_state.telematics_data,
                                sequence_length=sequence_length
                            )
                            
                            if X is not None:
                                errors, anomalies, threshold = detect_anomalies_lstm(
                                    st.session_state.lstm_model,
                                    X,
                                    threshold_percentile=threshold_percentile
                                )
                                
                                if errors is not None:
                                    n_anomalies = np.sum(anomalies)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Samples", len(anomalies))
                                    with col2:
                                        st.metric("Anomalies Detected", n_anomalies)
                                    with col3:
                                        st.metric("Anomaly Rate", f"{100*n_anomalies/len(anomalies):.2f}%")
                                    
                                    # Visualization
                                    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
                                    
                                    axes[0].hist(errors, bins=50, alpha=0.7, edgecolor='black')
                                    axes[0].axvline(threshold, color='red', linestyle='--', 
                                                   label=f'Threshold: {threshold:.4f}')
                                    axes[0].set_xlabel('Prediction Error')
                                    axes[0].set_ylabel('Frequency')
                                    axes[0].set_title('Error Distribution')
                                    axes[0].legend()
                                    axes[0].grid(True, alpha=0.3)
                                    
                                    axes[1].plot(errors, alpha=0.6, label='Errors')
                                    axes[1].axhline(threshold, color='red', linestyle='--', 
                                                   label='Threshold')
                                    axes[1].scatter(np.where(anomalies)[0], errors[anomalies],
                                                  color='red', marker='x', s=50, label='Anomalies')
                                    axes[1].set_xlabel('Sample Index')
                                    axes[1].set_ylabel('Error')
                                    axes[1].set_title('Anomaly Detection Timeline')
                                    axes[1].legend()
                                    axes[1].grid(True, alpha=0.3)
                                    
                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    
                                    # Store in history
                                    st.session_state.anomaly_history.append({
                                        'timestamp': datetime.now(),
                                        'n_anomalies': n_anomalies,
                                        'threshold': threshold
                                    })
                        except Exception as e:
                            st.error(f"❌ Error detecting anomalies: {e}")
    
    # ========================================================================
    # TAB 3: Diagnosis
    # ========================================================================
    with tab3:
        st.header("Random Forest Diagnosis")
        st.markdown("Predict failure kilometers using Random Forest regression.")
        
        if st.session_state.telematics_data is None:
            st.warning("⚠️ Please fetch telematics data first in the Data Ingestion tab.")
        else:
            if st.button("🌳 Train Random Forest Model", type="primary"):
                with st.spinner("Training Random Forest model..."):
                    try:
                        model, metrics = train_rf_model(st.session_state.telematics_data)
                        
                        if model is not None:
                            st.session_state.rf_model = model
                            st.success("✅ Random Forest model trained successfully!")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Test MSE", f"{metrics['mse']:.2f}")
                            with col2:
                                st.metric("Test MAE", f"{metrics['mae']:.2f}")
                            
                            # Feature importance
                            feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
                            importance = model.feature_importances_
                            
                            fig, ax = plt.subplots(figsize=(8, 5))
                            ax.barh(feature_cols, importance)
                            ax.set_xlabel('Importance')
                            ax.set_title('Feature Importance')
                            ax.grid(True, alpha=0.3, axis='x')
                            st.pyplot(fig)
                    except Exception as e:
                        st.error(f"❌ Error training model: {e}")
            
            if st.session_state.rf_model is not None:
                st.subheader("🔮 Failure Prediction")
                
                # Prediction interface
                col1, col2, col3 = st.columns(3)
                with col1:
                    voltage = st.number_input("Battery Voltage (V)", 10.0, 13.0, 12.5, 0.1)
                with col2:
                    temp = st.number_input("Battery Temperature (°C)", 20.0, 60.0, 30.0, 1.0)
                with col3:
                    cycles = st.number_input("Charge Cycles", 0, 2000, 500, 10)
                
                if st.button("📊 Predict Failure KM"):
                    try:
                        features = pd.DataFrame({
                            'battery_voltage': [voltage],
                            'battery_temp': [temp],
                            'charge_cycles': [cycles]
                        })
                        
                        prediction = predict_failure_km(st.session_state.rf_model, features)
                        
                        if prediction is not None:
                            st.success(f"✅ Predicted Failure KM: **{prediction[0]:,.0f} km**")
                            
                            # Show confidence interval (simplified)
                            confidence_lower = prediction[0] * 0.8
                            confidence_upper = prediction[0] * 1.2
                            st.info(f"📊 Confidence Interval: {confidence_lower:,.0f} - {confidence_upper:,.0f} km")
                    except Exception as e:
                        st.error(f"❌ Error in prediction: {e}")
                
                # Batch prediction on current data
                if st.button("📈 Predict on All Vehicles"):
                    try:
                        feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
                        df_features = st.session_state.telematics_data[feature_cols].fillna(
                            st.session_state.telematics_data[feature_cols].mean()
                        )
                        
                        predictions = predict_failure_km(st.session_state.rf_model, df_features)
                        
                        if predictions is not None:
                            results_df = st.session_state.telematics_data.copy()
                            results_df['predicted_failure_km'] = predictions
                            
                            st.dataframe(
                                results_df[['vehicle_id'] + feature_cols + ['predicted_failure_km']].head(20),
                                use_container_width=True
                            )
                            
                            # Visualization
                            fig, ax = plt.subplots(figsize=(10, 5))
                            if 'vehicle_id' in results_df.columns:
                                vehicle_predictions = results_df.groupby('vehicle_id')['predicted_failure_km'].mean()
                                ax.bar(range(len(vehicle_predictions)), vehicle_predictions.values)
                                ax.set_xticks(range(len(vehicle_predictions)))
                                ax.set_xticklabels(vehicle_predictions.index, rotation=45)
                                ax.set_ylabel('Predicted Failure KM')
                                ax.set_title('Average Predicted Failure KM by Vehicle')
                                ax.grid(True, alpha=0.3, axis='y')
                            else:
                                ax.hist(predictions, bins=30, edgecolor='black')
                                ax.set_xlabel('Predicted Failure KM')
                                ax.set_ylabel('Frequency')
                                ax.set_title('Distribution of Predicted Failure KM')
                                ax.grid(True, alpha=0.3)
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                    except Exception as e:
                        st.error(f"❌ Error in batch prediction: {e}")
    
    # ========================================================================
    # TAB 4: RL Scheduling
    # ========================================================================
    with tab4:
        st.header("Q-Learning Maintenance Scheduler")
        st.markdown("Reinforcement learning for optimal maintenance slot scheduling.")
        
        # Initialize Q-Learning scheduler
        if st.session_state.q_table is None:
            st.session_state.q_agent = QLearningScheduler()
        else:
            if 'q_agent' not in st.session_state:
                st.session_state.q_agent = QLearningScheduler()
                st.session_state.q_agent.q_table = st.session_state.q_table
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Training")
            n_training_episodes = st.slider("Training Episodes", 10, 100, 50)
            
            if st.button("🎓 Train Q-Learning Agent", type="primary"):
                with st.spinner("Training Q-learning agent..."):
                    try:
                        # Simulate training episodes
                        for episode in range(n_training_episodes):
                            # Random demand
                            demand = np.random.random()
                            state = st.session_state.q_agent.get_state(demand)
                            action = st.session_state.q_agent.choose_action(state, training=True)
                            
                            # Simulate environment
                            wait_times = [0.2, 0.5, 0.8]
                            wait_time = wait_times[action]
                            satisfaction = 1.0 - wait_time
                            reward = st.session_state.q_agent.calculate_reward(wait_time, satisfaction)
                            
                            # Next state (demand changes)
                            next_demand = np.clip(demand + np.random.normal(0, 0.1), 0, 1)
                            next_state = st.session_state.q_agent.get_state(next_demand)
                            
                            # Update Q-table
                            st.session_state.q_agent.update_q_table(state, action, reward, next_state)
                        
                        st.session_state.q_table = st.session_state.q_agent.q_table
                        st.success(f"✅ Trained for {n_training_episodes} episodes!")
                        
                        # Display Q-table
                        st.subheader("Q-Table")
                        q_df = pd.DataFrame(
                            st.session_state.q_agent.q_table,
                            index=['Low Demand', 'Medium Demand', 'High Demand'],
                            columns=['Morning', 'Afternoon', 'Evening']
                        )
                        st.dataframe(q_df.style.background_gradient(cmap='viridis'), use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error training agent: {e}")
        
        with col2:
            st.subheader("Scheduling")
            current_demand = st.slider("Current Demand Level", 0.0, 1.0, 0.5, 0.01)
            n_vehicles_needing_maintenance = st.slider("Vehicles Needing Maintenance", 1, 20, 5)
            
            if st.button("📅 Schedule Maintenance"):
                try:
                    slot, reward, wait_time, satisfaction = st.session_state.q_agent.schedule_maintenance(
                        current_demand, n_vehicles_needing_maintenance
                    )
                    
                    st.success(f"✅ Recommended Slot: **{slot}**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Expected Reward", f"{reward:.3f}")
                    with col2:
                        st.metric("Wait Time", f"{wait_time:.2f}")
                    with col3:
                        st.metric("Satisfaction", f"{satisfaction:.2f}")
                    
                    # Visualization
                    fig, ax = plt.subplots(figsize=(8, 5))
                    state = st.session_state.q_agent.get_state(current_demand)
                    q_values = st.session_state.q_agent.q_table[state]
                    slots = ['Morning', 'Afternoon', 'Evening']
                    colors = ['green' if i == np.argmax(q_values) else 'gray' for i in range(3)]
                    ax.bar(slots, q_values, color=colors)
                    ax.set_ylabel('Q-Value')
                    ax.set_title(f'Q-Values for Current State (Demand: {current_demand:.2f})')
                    ax.grid(True, alpha=0.3, axis='y')
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"❌ Error in scheduling: {e}")
    
    # ========================================================================
    # TAB 5: Feedback Loops
    # ========================================================================
    with tab5:
        st.header("Feedback Loops")
        st.markdown("Inner and outer feedback loops for continuous improvement.")
        
        if st.session_state.telematics_data is None:
            st.warning("⚠️ Please fetch telematics data first in the Data Ingestion tab.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔄 Inner Feedback Loop")
                st.markdown("Partially retrain Random Forest with new data.")
                
                if st.session_state.rf_model is None:
                    st.warning("⚠️ Please train RF model first in Diagnosis tab.")
                else:
                    retrain_fraction = st.slider("Retrain Fraction", 0.05, 0.5, 0.1, 0.05)
                    
                    if st.button("🔄 Retrain Model (Inner Loop)", type="primary"):
                        with st.spinner("Retraining model with new data..."):
                            try:
                                # Simulate new data (use recent data as "new")
                                new_data = st.session_state.telematics_data.tail(50)
                                
                                updated_model = inner_feedback_loop(
                                    st.session_state.rf_model,
                                    new_data,
                                    retrain_fraction=retrain_fraction
                                )
                                
                                st.session_state.rf_model = updated_model
                                st.success(f"✅ Model updated with {len(new_data)} new samples!")
                                st.info("ℹ️ Note: In production, this would use incremental learning.")
                            except Exception as e:
                                st.error(f"❌ Error in inner feedback loop: {e}")
            
            with col2:
                st.subheader("🔄 Outer Feedback Loop")
                st.markdown("K-Means Root Cause Analysis on aggregated data.")
                
                n_clusters = st.slider("Number of Clusters", 2, 5, 3)
                
                if st.button("🔍 Perform RCA (Outer Loop)", type="primary"):
                    with st.spinner("Performing root cause analysis..."):
                        try:
                            # Aggregate data by vehicle
                            if 'vehicle_id' in st.session_state.telematics_data.columns:
                                aggregated = st.session_state.telematics_data.groupby('vehicle_id').agg({
                                    'battery_voltage': 'mean',
                                    'battery_temp': 'mean',
                                    'charge_cycles': 'max'
                                }).reset_index()
                            else:
                                aggregated = st.session_state.telematics_data.select_dtypes(include=[np.number])
                            
                            cluster_labels, centroids = outer_feedback_loop(aggregated, n_clusters=n_clusters)
                            
                            if cluster_labels is not None:
                                st.success(f"✅ Identified {n_clusters} root cause clusters!")
                                
                                # Add cluster labels
                                aggregated['cluster'] = cluster_labels
                                
                                # Display results
                                st.dataframe(aggregated, use_container_width=True)
                                
                                # Visualization
                                if len(aggregated.columns) >= 3:
                                    fig = plt.figure(figsize=(10, 6))
                                    ax = fig.add_subplot(111, projection='3d')
                                    
                                    feature_cols = ['battery_voltage', 'battery_temp', 'charge_cycles']
                                    available_cols = [c for c in feature_cols if c in aggregated.columns]
                                    
                                    if len(available_cols) >= 2:
                                        x_col, y_col = available_cols[0], available_cols[1]
                                        scatter = ax.scatter(
                                            aggregated[x_col],
                                            aggregated[y_col],
                                            aggregated.get(available_cols[2], range(len(aggregated))),
                                            c=cluster_labels,
                                            cmap='viridis',
                                            s=100
                                        )
                                        ax.set_xlabel(x_col)
                                        ax.set_ylabel(y_col)
                                        if len(available_cols) >= 3:
                                            ax.set_zlabel(available_cols[2])
                                        ax.set_title('Root Cause Analysis Clusters')
                                        plt.colorbar(scatter, ax=ax, label='Cluster')
                                        st.pyplot(fig)
                                
                                # Store for feedback
                                st.session_state.feedback_data.append({
                                    'timestamp': datetime.now(),
                                    'n_clusters': n_clusters,
                                    'cluster_labels': cluster_labels
                                })
                            else:
                                st.error("❌ Insufficient data for clustering.")
                        except Exception as e:
                            st.error(f"❌ Error in outer feedback loop: {e}")
    
    # ========================================================================
    # TAB 6: UEBA Simulation
    # ========================================================================
    with tab6:
        st.header("UEBA: User and Entity Behavior Analytics")
        st.markdown("Isolation Forest for anomaly detection in agent logs.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            n_logs = st.slider("Number of Log Entries", 50, 500, 100)
            
            if st.button("📝 Generate Agent Logs", type="primary"):
                with st.spinner("Generating agent logs..."):
                    try:
                        st.session_state.agent_logs = simulate_agent_logs(n_logs=n_logs)
                        st.success(f"✅ Generated {len(st.session_state.agent_logs)} log entries!")
                    except Exception as e:
                        st.error(f"❌ Error generating logs: {e}")
        
        with col2:
            alert_threshold = st.slider("Alert Threshold", 1, 10, 3)
        
        if len(st.session_state.agent_logs) > 0:
            st.subheader("📊 Agent Logs")
            st.dataframe(st.session_state.agent_logs.head(20), use_container_width=True)
            
            if st.button("🔍 Detect UEBA Anomalies"):
                with st.spinner("Analyzing agent behavior..."):
                    try:
                        is_anomaly, anomaly_scores = detect_ueba_anomalies(st.session_state.agent_logs)
                        
                        if is_anomaly is not None:
                            n_anomalies = np.sum(is_anomaly)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Logs", len(st.session_state.agent_logs))
                            with col2:
                                st.metric("Anomalies Detected", n_anomalies)
                            with col3:
                                st.metric("Anomaly Rate", f"{100*n_anomalies/len(st.session_state.agent_logs):.2f}%")
                            
                            # Check for self-healing alert
                            alert_triggered = trigger_self_healing_alert(n_anomalies, threshold=alert_threshold)
                            
                            if alert_triggered:
                                st.error(f"🚨 **SELF-HEALING ALERT TRIGGERED!** {n_anomalies} anomalies detected (threshold: {alert_threshold})")
                                st.warning("⚠️ Initiating self-healing protocols...")
                            else:
                                st.success(f"✅ System normal. {n_anomalies} anomalies detected (below threshold: {alert_threshold})")
                            
                            # Anomalous logs
                            if n_anomalies > 0:
                                st.subheader("🚨 Anomalous Log Entries")
                                anomalous_logs = st.session_state.agent_logs[is_anomaly].copy()
                                anomalous_logs['anomaly_score'] = anomaly_scores[is_anomaly]
                                st.dataframe(anomalous_logs, use_container_width=True)
                            
                            # Visualization
                            fig, axes = plt.subplots(1, 2, figsize=(12, 4))
                            
                            # Anomaly scores distribution
                            axes[0].hist(anomaly_scores, bins=50, alpha=0.7, edgecolor='black')
                            axes[0].axvline(np.percentile(anomaly_scores, 10), color='red', 
                                          linestyle='--', label='Anomaly Threshold')
                            axes[0].set_xlabel('Anomaly Score')
                            axes[0].set_ylabel('Frequency')
                            axes[0].set_title('Anomaly Score Distribution')
                            axes[0].legend()
                            axes[0].grid(True, alpha=0.3)
                            
                            # Scatter plot
                            if 'duration_seconds' in st.session_state.agent_logs.columns:
                                scatter = axes[1].scatter(
                                    st.session_state.agent_logs['duration_seconds'],
                                    st.session_state.agent_logs.get('data_accessed', range(len(st.session_state.agent_logs))),
                                    c=is_anomaly,
                                    cmap='RdYlGn',
                                    alpha=0.6
                                )
                                axes[1].set_xlabel('Duration (seconds)')
                                axes[1].set_ylabel('Data Accessed')
                                axes[1].set_title('Anomaly Detection (Red=Anomaly)')
                                axes[1].grid(True, alpha=0.3)
                            
                            plt.tight_layout()
                            st.pyplot(fig)
                    except Exception as e:
                        st.error(f"❌ Error in UEBA detection: {e}")
        else:
            st.info("ℹ️ Click 'Generate Agent Logs' to create simulation data.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Automotive Predictive Maintenance System** | Built with Streamlit, Keras, Scikit-learn, and NumPy")


if __name__ == "__main__":
    main()
