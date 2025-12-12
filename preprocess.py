# preprocess_ai4i.py
# Clean + preprocess AI4I 2020 predictive maintenance dataset for ML training

import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import numpy as np
import os

def preprocess_ai4i(input_path="ai4i2020.csv",
                    output_path="ai4i_processed.csv",
                    scale_features=False):
    print("Loading dataset...")
    df = pd.read_csv(input_path)

    # -------------------------------------------------------------------
    # 1. Clean column names (remove spaces & brackets)
    # -------------------------------------------------------------------
    df.columns = (
        df.columns
        .str.replace(" ", "_")
        .str.replace("[", "")
        .str.replace("]", "")
        .str.replace("/", "_")
        .str.replace(".", "")
    )

    # -------------------------------------------------------------------
    # 1.5 Feature Engineering (Physics-Based)
    # -------------------------------------------------------------------
    print("Adding derived features...")
    # Power (W) = Torque (Nm) * RPM * (2*pi/60)
    df["Power_W"] = df["Torque_Nm"] * df["Rotational_speed_rpm"] * 0.1047
    
    # Overstrain Index = Torque * Tool Wear (Proxy for cumulative stress)
    df["Strain_Index"] = df["Torque_Nm"] * df["Tool_wear_min"]
    
    # Temperature Difference
    df["Temp_Diff"] = df["Process_temperature_K"] - df["Air_temperature_K"]

    # -------------------------------------------------------------------
    # 2. Encode Machine Type (M/L/H)
    # -------------------------------------------------------------------
    print("Encoding 'Type' column...")
    le = LabelEncoder()
    df["Type"] = le.fit_transform(df["Type"])   # M=0, L=1, H=2

    # -------------------------------------------------------------------
    # 3. Create unified failure class label
    # -------------------------------------------------------------------
    print("Creating multi-class label 'failure_class'...")

    df["failure_class"] = 0
    df.loc[df["HDF"] == 1, "failure_class"] = 1      # cooling failure
    df.loc[df["PWF"] == 1, "failure_class"] = 2      # battery/power failure
    df.loc[df["TWF"] == 1, "failure_class"] = 3      # vibration/tool failure
    df.loc[df["OSF"] == 1, "failure_class"] = 4      # engine stress
    
    # RNF (random failure) -> keep separate or merge
    # df.loc[df["RNF"] == 1, "failure_class"] = 4

    # -------------------------------------------------------------------
    # 4. Remove columns not useful for training
    # -------------------------------------------------------------------
    drop_cols = ["UDI", "Product_ID", "Machine_failure",
                 "TWF", "HDF", "PWF", "OSF", "RNF"]  # already encoded

    df = df.drop(columns=drop_cols)

    # -------------------------------------------------------------------
    # 5. OPTIONAL: Feature scaling (StandardScaler)
    # -------------------------------------------------------------------
    if scale_features:
        print("Scaling numerical features...")
        feature_cols = [c for c in df.columns if c not in ["failure_class"]]
        scaler = StandardScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
        pd.to_pickle(scaler, "models/ai4i_scaler.pkl")
        print("Saved scaler -> models/ai4i_scaler.pkl")

    # -------------------------------------------------------------------
    # 6. Save processed dataset
    # -------------------------------------------------------------------
    df.to_csv(output_path, index=False)
    print(f"Preprocessed dataset saved -> {output_path}")
    print("Rows:", len(df))

    # -------------------------------------------------------------------
    # 7. Return train-ready data
    # -------------------------------------------------------------------
    X = df.drop(columns=["failure_class"])
    y = df["failure_class"]

    return X, y, df


if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    X, y, df_clean = preprocess_ai4i(scale_features=False)
    print("\nSample output:")
    print(df_clean.head())
