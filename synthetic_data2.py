# generate_multiclass_data.py
# Generates synthetic multi-class predictive maintenance dataset

import pandas as pd
import random
import numpy as np

# --------------------------------------------------------------
# Component Labels
# --------------------------------------------------------------
COMPONENTS = {
    0: "normal",
    1: "cooling_failure",
    2: "battery_failure",
    3: "vibration_failure",
    4: "engine_stress"
}

def generate_row():
    # Raw features
    engine_temp = random.uniform(80, 120)
    battery_voltage = random.uniform(10.5, 13.0)
    vibration = random.uniform(0.1, 1.5)
    coolant_temp = random.uniform(75, 115)
    dtc_flag = 1 if random.random() < 0.1 else 0
    mileage = random.randint(10000, 90000)

    # Derived features
    engine_temp_avg = engine_temp - random.uniform(-4, 4)
    engine_temp_std = random.uniform(2, 6)
    battery_avg = battery_voltage + random.uniform(-0.2, 0.2)
    battery_drop = random.uniform(0, 1)
    temp_rise_rate = random.uniform(-4, 10)
    coolant_rise_rate = random.uniform(-4, 10)
    vibration_std = random.uniform(0.05, 0.5)

    # ---------------------------------------------------------------------
    # Multi-class label generation logic (very important)
    # ---------------------------------------------------------------------
    # 0 = normal
    label = 0

    # 1 = cooling system failure
    if engine_temp > 105 or coolant_rise_rate > 6:
        label = 1

    # 2 = battery failure
    if battery_voltage < 11.5 or battery_drop > 0.4:
        label = 2

    # 3 = vibration failure
    if vibration > 1.0 or vibration_std > 0.4:
        label = 3

    # 4 = general engine stress
    if temp_rise_rate > 5 and engine_temp_avg > 98:
        label = 4

    return [
        engine_temp, battery_voltage, vibration, coolant_temp,
        engine_temp_avg, engine_temp_std, battery_avg, battery_drop,
        temp_rise_rate, coolant_rise_rate, vibration_std,
        dtc_flag, mileage, label
    ]


def generate_dataset(n=5000):
    rows = [generate_row() for _ in range(n)]
    cols = [
        "engine_temp","battery_voltage","vibration","coolant_temp",
        "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
        "temp_rise_rate","coolant_rise_rate","vibration_std",
        "dtc_flag","mileage","failure_class"
    ]

    df = pd.DataFrame(rows, columns=cols)
    df.to_csv("training_multiclass_data.csv", index=False)
    print("Saved → training_multiclass_data.csv")


if __name__ == "__main__":
    generate_dataset()
