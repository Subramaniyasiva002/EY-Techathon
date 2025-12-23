# refinement_train_new_model.py
# Incremental Training: Combine original dataset with live feedback samples

import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

print("=" * 60)
print("MODEL REFINEMENT WITH LIVE FEEDBACK DATA")
print("=" * 60)

# -------------------------------------------------------------------
# 1. Load Original Processed Dataset
# -------------------------------------------------------------------
original_df = pd.read_csv("ai4i_processed.csv")
print(f"\n[1/6] Loaded original dataset: {original_df.shape[0]} rows")

# -------------------------------------------------------------------
# 2. Load Live Samples (Real-World Data from Dashboard)
# -------------------------------------------------------------------
live_df = pd.read_csv("live_feature_samples.csv")
print(f"[2/6] Loaded live samples: {live_df.shape[0]} rows")

# Filter only samples with actual_failure labels (technician verified)
live_df = live_df[live_df['actual_failure'].notna() & (live_df['actual_failure'] != '')]
print(f"      Labeled samples: {live_df.shape[0]} rows")

if live_df.shape[0] == 0:
    print("\n⚠️  No labeled samples found in live_feature_samples.csv")
    print("   Please complete more services and collect feedback first.")
    exit()

# -------------------------------------------------------------------
# 3. Map Failure Names to Class Numbers
# -------------------------------------------------------------------
failure_map = {
    "Heat Dissipation Failure": 1,
    "Power/Battery Failure": 2,
    "Tool Wear/Vibration Failure": 3,
    "Overstrain Failure": 4,
    "No Failure": 0
}

live_df['failure_class'] = live_df['actual_failure'].map(failure_map)

# Handle unmapped labels
unmapped = live_df[live_df['failure_class'].isna()]
if len(unmapped) > 0:
    print(f"\n⚠️  Warning: {len(unmapped)} samples have unmapped labels:")
    print(unmapped['actual_failure'].unique())
    live_df = live_df[live_df['failure_class'].notna()]

print(f"[3/6] Mapped failure labels to classes")

# -------------------------------------------------------------------
# 4. Feature Engineering (Match Training Pipeline)
# -------------------------------------------------------------------
features = ['Type', 'Air_temperature_K', 'Process_temperature_K', 
            'Rotational_speed_rpm', 'Torque_Nm', 'Tool_wear_min']

# Compute derived physics features
live_df['Power_W'] = live_df['Torque_Nm'] * live_df['Rotational_speed_rpm'] * 0.1047
live_df['Strain_Index'] = live_df['Torque_Nm'] * live_df['Tool_wear_min']
live_df['Temp_Diff'] = live_df['Process_temperature_K'] - live_df['Air_temperature_K']

features += ['Power_W', 'Strain_Index', 'Temp_Diff']

print(f"[4/6] Computed derived features")

# -------------------------------------------------------------------
# 5. Combine Datasets
# -------------------------------------------------------------------
combined_df = pd.concat([
    original_df[features + ['failure_class']], 
    live_df[features + ['failure_class']]
], ignore_index=True)

print(f"[5/6] Combined dataset: {combined_df.shape[0]} rows")
print(f"      Original: {original_df.shape[0]}, Live: {live_df.shape[0]}")

# -------------------------------------------------------------------
# 6. Train Refined Model
# -------------------------------------------------------------------
X = combined_df[features]
y = combined_df['failure_class']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n[6/6] Training refined LightGBM model...")

model = LGBMClassifier(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=15,
    num_leaves=31,
    random_state=42,
    class_weight="balanced",
    objective="multiclass",
    num_class=5,
    importance_type="gain",
    verbose=-1  # Suppress training logs
)

model.fit(X_train, y_train)

# -------------------------------------------------------------------
# 7. Evaluation
# -------------------------------------------------------------------
pred = model.predict(X_test)

print("\n" + "=" * 60)
print("REFINED MODEL PERFORMANCE")
print("=" * 60)
print(f"\nAccuracy: {accuracy_score(y_test, pred):.3f}")
print("\nClassification Report:")
print(classification_report(y_test, pred, target_names=[
    "No Failure", "Heat Dissipation", "Power/Battery", 
    "Tool Wear/Vibration", "Overstrain"
]))

# -------------------------------------------------------------------
# 8. Save Refined Model
# -------------------------------------------------------------------
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/ai4i_lgbm_refined.joblib")

print("=" * 60)
print("[SUCCESS] REFINEMENT COMPLETE")
print("=" * 60)
print(f"\nSaved refined model -> models/ai4i_lgbm_refined.joblib")
print(f"\nTo use this model, update diagnosis_agent.py:")
print('   self.model = joblib.load("models/ai4i_lgbm_refined.joblib")')