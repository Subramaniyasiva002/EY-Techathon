# refinement_train_new_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
import os

# Load original synthetic training data
orig = pd.read_csv("training_multiclass_data.csv")

# Load new incremental data
new = pd.read_csv("incremental_training_data.csv")

# Merge datasets
full_data = pd.concat([orig, new], axis=0).reset_index(drop=True)

# Define features
FEATURES = [
    "engine_temp","battery_voltage","vibration","coolant_temp",
    "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
    "temp_rise_rate","coolant_rise_rate","vibration_std",
    "dtc_flag","mileage"
]

TARGET = "failure_class"

X = full_data[FEATURES]
y = full_data[TARGET]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
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

# Save updated model
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/rf_multiclass_model_updated.joblib")

print("\nUpdated model saved → rf_multiclass_model_updated.joblib")
