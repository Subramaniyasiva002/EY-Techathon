# forecasting_module.py
"""
Service demand forecasting module (lightweight).
- Reads maintenance_history_db.json
- Aggregates historical service completions by date (and by service_center if present)
- Trains a simple linear regression on daily counts and predicts next N days
- Writes results to service_forecast.json
- Provides helper to apply forecasts to a SchedulingAgent

Requires: pandas, scikit-learn
Run: python forecasting_module.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

DB_PATH = Path("maintenance_history_db.json")
OUT_PATH = Path("service_forecast.json")


def load_history(db_path=DB_PATH):
    """
    Load maintenance_history_db.json, return list of service records (dict).
    Tries to be robust to slightly different schemas.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path} not found")

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Data could be dict keyed by vehicle_id or list of records.
    records = []
    if isinstance(data, dict):
        # If top-level is per-vehicle: each key -> list of events
        for k, v in data.items():
            if isinstance(v, list):
                for rec in v:
                    # If vehicle id not in rec, add it
                    if isinstance(rec, dict) and "vehicle_id" not in rec:
                        rec["vehicle_id"] = k
                    records.append(rec)
            elif isinstance(v, dict):
                # maybe single record per vehicle
                rec = v.copy()
                rec["vehicle_id"] = k
                records.append(rec)
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("Unsupported maintenance_history_db.json format")

    # Normalize: attempt to collect a timestamp for each record
    cleaned = []
    for r in records:
        # Common timestamp key names
        ts = None
        for k in ("timestamp", "completed_at", "service_time", "date", "iso_time"):
            if k in r and r[k]:
                ts = r[k]
                break
        if ts is None:
            # If record contains booking_id and slot/time maybe present in nested booking object
            # Skip records without timestamp (can't include in daily counts)
            continue

        # Parse timestamps robustly
        parsed = None
        if isinstance(ts, (int, float)):
            # epoch seconds
            parsed = datetime.utcfromtimestamp(float(ts))
        else:
            # Try ISO parse
            try:
                parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                # Try common formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S"):
                    try:
                        parsed = datetime.strptime(str(ts), fmt)
                        break
                    except Exception:
                        continue
        if parsed is None:
            # skip if cannot parse
            continue

        # optional service_center
        sc = r.get("service_center") or r.get("center") or r.get("center_id") or r.get("service_center_id")
        cleaned.append({
            "vehicle_id": r.get("vehicle_id"),
            "timestamp": parsed,
            "service_center": sc,
            "outcome": r.get("outcome") or r.get("status") or r.get("result") or "completed"
        })

    return cleaned


def aggregate_daily(records):
    """
    Aggregate counts per date and per service_center if available.
    Returns:
      df_national: pandas Series indexed by date with total counts
      df_centers: dict of Series per center
    """
    if not records:
        return pd.Series(dtype=int), {}

    rows = []
    for r in records:
        # only count completed services
        if r.get("outcome") and str(r.get("outcome")).lower() in ("completed", "success", "done", "ok"):
            rows.append((r["timestamp"].date(), r.get("service_center") or "UNASSIGNED"))

    df = pd.DataFrame(rows, columns=["date", "center"])
    # national counts
    national = df.groupby("date").size().sort_index()
    # per center
    centers = {}
    for c, g in df.groupby("center"):
        centers[c] = g.groupby("date").size().sort_index()

    return national, centers


def create_time_features(series: pd.Series):
    """
    Create X,y for regression where X is day index (0..n-1) and y is count
    """
    series = series.sort_index()
    # fill missing dates with 0
    idx = pd.date_range(series.index.min(), series.index.max(), freq="D")
    series = series.reindex(idx, fill_value=0)
    X = np.arange(len(series)).reshape(-1, 1)  # day index
    y = series.values
    return X, y, series.index


def train_and_forecast(series: pd.Series, days_ahead=7, min_days=14):
    """
    Train linear regression on series and predict next days.
    If not enough historical days (<min_days), use moving average fallback.
    Returns dict: {date_str: predicted_count}
    """
    if series.empty:
        today = datetime.utcnow().date()
        return {str(today + timedelta(days=i)): 0 for i in range(1, days_ahead + 1)}

    X, y, idx = create_time_features(series)

    if len(y) < min_days or np.all(y == 0):
        # fallback: moving average of past 7 days
        window = min(7, max(1, len(y)))
        ma = float(np.mean(y[-window:])) if len(y) > 0 else 0.0
        base_date = idx[-1].date()
        return {str(base_date + timedelta(days=i)): float(round(ma, 2)) for i in range(1, days_ahead + 1)}

    model = LinearRegression()
    model.fit(X, y)
    last_idx = X[-1, 0]
    future_X = np.arange(last_idx + 1, last_idx + 1 + days_ahead).reshape(-1, 1)
    preds = model.predict(future_X)
    preds = np.clip(preds, 0, None)  # no negative predictions

    base_date = idx[-1].date()
    out = {}
    for i, p in enumerate(preds, start=1):
        out[str(base_date + timedelta(days=i))] = float(round(float(p), 2))
    return out


def generate_forecast(db_path=DB_PATH, days_ahead=7, out_path=OUT_PATH):
    records = load_history(db_path)
    national, centers = aggregate_daily(records)

    national_forecast = train_and_forecast(national, days_ahead=days_ahead)

    centers_forecast = {}
    for c, s in centers.items():
        centers_forecast[c] = train_and_forecast(s, days_ahead=days_ahead)

    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days_ahead": days_ahead,
        "national_forecast": national_forecast,
        "centers_forecast": centers_forecast,
        "historical_national": {str(d): int(v) for d, v in national.items()}
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Forecast saved to {out_path}")
    return result


# -------------------------
# Helper to integrate with SchedulingAgent
# -------------------------
def apply_forecast_to_scheduler(scheduler, forecast, threshold_factor=1.2):
    """
    Apply forecast to scheduler by adjusting center capacities or warning flags.
    scheduler: your SchedulingAgent instance (must have set_center_capacity or similar APIs)
    forecast: dict returned by generate_forecast()
    threshold_factor: float multiplier to mark overloaded centers
    """
    # Simple logic:
    # - For each center, compute average predicted per day over forecast horizon
    # - If avg_predicted > center_capacity * threshold_factor => mark overloaded
    centers_forecast = forecast.get("centers_forecast", {})
    # If scheduler has get_center_capacity(center) and set_center_flag(center, msg)
    for center, fc in centers_forecast.items():
        vals = list(fc.values())
        avg = sum(vals) / len(vals) if vals else 0.0
        cap = None
        try:
            cap = scheduler.get_center_capacity(center)
        except Exception:
            # if scheduler has no per-center capacity, try global
            try:
                cap = scheduler.get_global_capacity()
            except Exception:
                cap = None

        if cap is not None:
            if avg > cap * threshold_factor:
                msg = f"Forecasted avg {avg:.1f} > capacity {cap} (threshold {threshold_factor})"
                try:
                    scheduler.set_center_flag(center, "OVERLOAD_WARNING", msg)
                except Exception:
                    print(f"[Forecast->Scheduler] Center {center} overload (no setter): {msg}")
            else:
                # clear flag if exists
                try:
                    scheduler.clear_center_flag(center)
                except Exception:
                    pass
        else:
            # no capacity info: set global advisory
            try:
                scheduler.set_global_forecast_advisory(avg)
            except Exception:
                print(f"[Forecast->Scheduler] No capacity API; avg predicted per center {center}: {avg:.2f}")


# CLI entry
if __name__ == "__main__":
    print("Generating forecast (7 days)...")
    f = generate_forecast()
    print(json.dumps(f, indent=2))
