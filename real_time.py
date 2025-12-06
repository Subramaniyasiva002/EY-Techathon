from data_analysis_agent import DataAnalysisAgent
from diagnosis_agent import DiagnosisAgent
from master_agent import MasterAgent



# Example maintenance history; in a real system this could come from a DB/API
MAINTENANCE_HISTORY = {
    "VH001": {
        "last_service_km": 45000,
        "last_service_days_ago": 60,
        "num_repairs": 3,
        "last_failure_km": 42000,
    }
}


def diagnosis_callback(features):
    print("\n----- NEW WINDOW RECEIVED -----")
    print("Features:", features)

    # ML-based prediction
    diagnosis = diagnosis_agent.predict(features)
    print("Diagnosis:", diagnosis)

    # Decision engine
    action = master_agent.handle_diagnosis(diagnosis)
    print("Action:", action)

diagnosis_agent = DiagnosisAgent()
master_agent = MasterAgent()


# Create agent with maintenance context and start continuous analysis
agent = DataAnalysisAgent(maintenance_history=MAINTENANCE_HISTORY)

# Run for a single vehicle, e.g. VH001 (continuous loop)
agent.start(["VH005"], diagnosis_callback)