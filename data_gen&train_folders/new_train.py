# train_ai4i_multiclass.py
# Train a multi-class RandomForest model using the preprocessed AI4I dataset

import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib, json, os

# -------------------------------------------------------------------
# 1. Load preprocessed dataset
# -------------------------------------------------------------------
DATA_PATH = "ai4i_processed.csv"
df = pd.read_csv(DATA_PATH)

print(f"Loaded processed dataset: {df.shape[0]} rows, {df.shape[1]} columns")

# -------------------------------------------------------------------
# 2. Define features + target
# -------------------------------------------------------------------
TARGET = "failure_class"
FEATURES = [c for c in df.columns if c != TARGET]

X = df[FEATURES]
y = df[TARGET]

print("Using features:", FEATURES)

# -------------------------------------------------------------------
# 3. Train/Test Split
# -------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------------------------------------------
# 4. LightGBM Multi-Class Model
# -------------------------------------------------------------------
print("\nTraining LightGBM Multi-Class Model...")

model = LGBMClassifier(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=15,
    num_leaves=31,
    random_state=42,
    class_weight="balanced",
    objective="multiclass",
    num_class=5,
    importance_type="gain"
)

model.fit(X_train, y_train)

# -------------------------------------------------------------------
# 5. Evaluation
# -------------------------------------------------------------------
pred = model.predict(X_test)

print("\nModel Accuracy:", accuracy_score(y_test, pred))
print("\nClassification Report:")
print(classification_report(y_test, pred))

# -------------------------------------------------------------------
# 6. Save Model + Metadata
# -------------------------------------------------------------------
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/ai4i_lgbm_model.joblib")
print("\nSaved model -> models/ai4i_lgbm_model.joblib")

with open("models/ai4i_features.json", "w") as f:
    json.dump(FEATURES, f, indent=4)
print("Saved feature order -> models/ai4i_features.json")

CLASS_MAP = {
    0: "normal",
    1: "cooling_failure",
    2: "battery_failure",
    3: "vibration_failure",
    4: "engine_stress"
}

with open("models/ai4i_class_map.json", "w") as f:
    json.dump(CLASS_MAP, f, indent=4)
print("Saved class map -> models/ai4i_class_map.json")

print("\nTraining Complete!")
