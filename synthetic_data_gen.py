# generate_training_data.py
# Creates synthetic training rows that match your real-time DataAnalysisAgent features
# You will train the RF model on this CSV

import pandas as pd
import random
import numpy as np

def generate_row():
    # ----- 1. Raw values -----
    engine_temp = random.uniform(80, 120)
    battery_voltage = random.uniform(10.5, 13.0)
    vibration = random.uniform(0.1, 1.5)
    coolant_temp = random.uniform(75, 115)
    dtc_flag = 1 if random.random() < 0.15 else 0
    
    # ----- 2. Rolling / Features -----
    engine_temp_avg = engine_temp - random.uniform(-5, 5)
    engine_temp_std = random.uniform(2, 6)
    battery_avg = battery_voltage + random.uniform(-0.3, 0.3)
    battery_drop = random.uniform(0, 1)
    temp_rise_rate = random.uniform(-5, 12)
    coolant_rise_rate = random.uniform(-5, 12)
    vibration_std = random.uniform(0.05, 0.4)
    
    mileage = random.randint(10000, 90000)
    
    # ----- LABEL (failure = 1) -----
    failure = 0
    if engine_temp > 105: failure = 1
    if battery_voltage < 11.5: failure = 1
    if vibration > 1.0: failure = 1
    if dtc_flag == 1: failure = 1
    
    return [
        engine_temp, battery_voltage, vibration, coolant_temp,
        engine_temp_avg, engine_temp_std, battery_avg, battery_drop,
        temp_rise_rate, coolant_rise_rate, vibration_std,
        dtc_flag, mileage, failure
    ]

def generate_dataset(n=5000):
    rows = [generate_row() for _ in range(n)]
    cols = [
        "engine_temp","battery_voltage","vibration","coolant_temp",
        "engine_temp_avg","engine_temp_std","battery_avg","battery_drop",
        "temp_rise_rate","coolant_rise_rate","vibration_std",
        "dtc_flag","mileage","failure"
    ]
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv("training_data.csv", index=False)
    print("training_data.csv saved with", len(df), "rows.")

if __name__ == "__main__":
    generate_dataset()
