# train_multiclass_rf.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib, json, os

DATA_PATH = "training_multiclass_data.csv"

df = pd.read_csv(DATA_PATH)

FEATURES = [
    "engine_temp","battery_voltage","vibration","coolant_temp",
    "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
    "temp_rise_rate","coolant_rise_rate","vibration_std",
    "dtc_flag","mileage"
]

TARGET = "failure_class"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, pred))
print("\nClassification Report:")
print(classification_report(y_test, pred))

# SAVE MODEL
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/rf_multiclass_model.joblib")
with open("models/rf_features.json", "w") as f:
    json.dump(FEATURES, f, indent=4)
with open("models/rf_class_map.json", "w") as f:
    json.dump({
        0:"normal",
        1:"cooling_failure",
        2:"battery_failure",
        3:"vibration_failure",
        4:"engine_stress"
    }, f, indent=4)

print("\nModel saved → models/rf_multiclass_model.joblib")
