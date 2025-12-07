# outer_loop_agents.py
import json
import pandas as pd
from forecasting_module import generate_forecast

class AggregateDataAgent:
    def run(self, state):
        print("[OuterLoop] Aggregating fleet data...")

        # Load maintenance history
        with open("maintenance_history_db.json") as f:
            hist = json.load(f)

        state["history"] = hist

        # Try loading live samples
        try:
            df_live = pd.read_csv("live_feature_samples.csv")
            print("[OuterLoop] Loaded live_feature_samples.csv")
        except FileNotFoundError:
            print("[OuterLoop] WARNING: live_feature_samples.csv not found. Using empty DataFrame.")
            df_live = pd.DataFrame()

        state["live_samples"] = df_live

        return state



class ForecastingAgent:
    def run(self, state):
        print("[OuterLoop] Running demand forecasting...")
        forecast = generate_forecast()
        state["forecast"] = forecast
        return state


class RCAAnalyticsAgent:
    def run(self, state):
        print("[OuterLoop] Running RCA analytics...")

        df = state.get("live_samples", pd.DataFrame())

        # CASE 1: No predictions available =====================================
        if df.empty:
            print("[OuterLoop] No live predictions found. Using default stats.")

            state["component_stats"] = {
                "normal": 0,
                "cooling_failure": 0,
                "battery_failure": 0,
                "vibration_failure": 0
            }
            return state
        # ======================================================================

        # CASE 2: Predictions exist
        comp_counts = df["predicted_class"].value_counts().to_dict()

        class_map = {
            0: "normal",
            1: "cooling_failure",
            2: "battery_failure",
            3: "vibration_failure"
        }

        component_stats = {class_map[k]: v for k, v in comp_counts.items()}

        # Ensure all components exist even if zero
        for comp in class_map.values():
            component_stats.setdefault(comp, 0)

        state["component_stats"] = component_stats
        return state


class ManufacturingSummaryAgent:
    def run(self, state):
        print("[OuterLoop] Generating manufacturing insights...")

        component_stats = state.get("component_stats", {})

        summary = {
            "top_failures": component_stats,
            "forecast_trends": state.get("forecast", {}).get("national_forecast", {}),
            "recommendations": [
                "Improve coolant hose quality",
                "Add real-time battery degradation monitor",
                "Inspect wheel bearing material specification"
            ]
        }

        with open("manufacturing_insights.json", "w") as f:
            json.dump(summary, f, indent=2)

        state["summary"] = summary
        return state
