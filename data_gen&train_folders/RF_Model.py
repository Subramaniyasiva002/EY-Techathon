# train_rf.py
# Trains a RandomForest model using training_data.csv and saves it as rf_model.joblib

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import os

# -------------------------------------------------------
# 1. Load training data
# -------------------------------------------------------
DATA_PATH = "training_data.csv"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError("training_data.csv not found. Generate data first!")

df = pd.read_csv(DATA_PATH)

# -------------------------------------------------------
# 2. Define features (🔴 MUST MATCH real-time DataAnalysisAgent keys)
# -------------------------------------------------------
FEATURES = [
    "engine_temp",
    "battery_voltage",
    "vibration",
    "coolant_temp",
    "engine_temp_avg",
    "engine_temp_std",
    "battery_avg",
    "battery_drop",
    "temp_rise_rate",
    "coolant_rise_rate",
    "vibration_std",
    "dtc_flag",
    "mileage"
]

TARGET = "failure"

X = df[FEATURES]
y = df[TARGET]

# -------------------------------------------------------
# 3. Train/Test split
# -------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------------------------------
# 4. Train RandomForest
# -------------------------------------------------------
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42
)

rf.fit(X_train, y_train)

# -------------------------------------------------------
# 5. Evaluate model
# -------------------------------------------------------
pred = rf.predict(X_test)
prob = rf.predict_proba(X_test)[:, 1]

print("\n============================================")
print("TRAINING COMPLETE – RandomForest Model")
print("============================================")
print("Accuracy:", accuracy_score(y_test, pred))
print("\nClassification Report:")
print(classification_report(y_test, pred))

# -------------------------------------------------------
# 6. Save model + feature order
# -------------------------------------------------------
os.makedirs("models", exist_ok=True)

joblib.dump(rf, "models/rf_model.joblib")
print("\nSaved model → models/rf_model.joblib")

with open("models/rf_features.json", "w") as f:
    json.dump(FEATURES, f, indent=4)
print("Saved feature order → models/rf_features.json")

print("\nAll done!")
