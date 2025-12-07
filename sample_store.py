# sample_store.py  for model refinement --
import csv
import os

class SampleStore:
    def __init__(self, file_path="live_feature_samples.csv"):
        self.file_path = file_path

        # create file with headers if not exists
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "vehicle_id",

                    # feature columns (align with RF features)
                    "engine_temp","battery_voltage","vibration","coolant_temp",
                    "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
                    "temp_rise_rate","coolant_rise_rate","vibration_std",
                    "dtc_flag","mileage",

                    # prediction info
                    "predicted_class",
                    "risk_score",

                    # actual label (unknown now)
                    "actual_failure"
                ])

    def save_sample(self, features, diagnosis):
        row = [
            features.get("timestamp"),
            features.get("vehicle_id"),

            features.get("engine_temp"),
            features.get("battery_voltage"),
            features.get("vibration"),
            features.get("coolant_temp"),
            features.get("engine_temp_avg"),
            features.get("engine_temp_std"),
            features.get("battery_avg"),
            features.get("battery_drop"),
            features.get("temp_rise_rate"),
            features.get("coolant_rise_rate"),
            features.get("vibration_std"),
            features.get("dtc_flag"),
            features.get("mileage"),

            diagnosis["predicted_class"],
            diagnosis["risk_score"],

            None  # true label added later after service
        ]

        with open(self.file_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
