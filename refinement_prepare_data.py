# refinement_prepare_data.py
import pandas as pd

# Load live incremental samples
live = pd.read_csv("live_feature_samples.csv")

# Keep only rows where actual_failure is NOT empty
live = live[live["actual_failure"].notna()]
live = live[live["actual_failure"].astype(str).str.lower().isin(
    ["battery_failure","cooling_failure","vibration_failure","engine_stress","normal"]
)]

# Map class names to numeric labels
class_map = {
    "normal": 0,
    "cooling_failure": 1,
    "battery_failure": 2,
    "vibration_failure": 3,
    "engine_stress": 4
}

live["failure_class"] = live["actual_failure"].apply(lambda x: class_map[x])

# Keep only RF feature columns
rf_features = [
    "engine_temp","battery_voltage","vibration","coolant_temp",
    "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
    "temp_rise_rate","coolant_rise_rate","vibration_std",
    "dtc_flag","mileage","failure_class"
]

live_refined = live[rf_features]

# Save to new incremental dataset
live_refined.to_csv("incremental_training_data.csv", index=False)

print("\nExtracted usable samples → incremental_training_data.csv")
print(live_refined.head())
