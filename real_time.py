from data_analysis_agent import DataAnalysisAgent
from diagnosis_agent import DiagnosisAgent
from sample_store import SampleStore

from state_model import VehicleState
from orchestration_graph import final_graph

diagnosis_agent = DiagnosisAgent()
sample_store = SampleStore()

def diagnosis_callback(features):
    print("\n--- NEW WINDOW ---")
    print(features)

    diagnosis = diagnosis_agent.predict(features)
    print("Diagnosis:", diagnosis)

    sample_store.save_sample(features, diagnosis)

    state = VehicleState(
        vehicle_id=features["vehicle_id"],
        features=features,
        diagnosis=diagnosis
    )

    final_graph.invoke(state)


# RUN TELEMATICS
MAINT_HISTORY = {
    "VH001": {"last_service_km": 45000, "last_service_days_ago": 60, "num_repairs": 3, "last_failure_km": 42000},
}

agent = DataAnalysisAgent(maintenance_history=MAINT_HISTORY)
agent.start(["VH001", "VH005"], diagnosis_callback)
