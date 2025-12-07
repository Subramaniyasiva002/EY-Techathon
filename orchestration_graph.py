from langgraph.graph import StateGraph
from state_model import VehicleState
from master_agent import (
    rca_step,
    customer_step,
    scheduling_step,
    booking_step,
    feedback_step,
)

graph = StateGraph(VehicleState)

# Add nodes
graph.add_node("SCHEDULING", scheduling_step)
graph.add_node("CUSTOMER", customer_step)
graph.add_node("BOOKING", booking_step)
graph.add_node("FEEDBACK", feedback_step)
graph.add_node("RCA", rca_step)
graph.add_node("END", lambda s: s)   # TERMINATION NODE


# Entry point
graph.set_entry_point("SCHEDULING")


# -------------------------------
# CONDITIONAL EDGE LOGIC
# -------------------------------
def schedule_router(state):
    pr = state["diagnosis"]["priority"]

    if pr == "LOW":
        return "RCA"      # mild check then stop
    return "CUSTOMER"      # continue normal flow


graph.add_conditional_edges("SCHEDULING", schedule_router)


# CUSTOMER NODE CONDITIONAL
def customer_router(state):
    if state.get("confirmed") is False:
        return "END"   # customer declined → stop pipeline
    return "BOOKING"


graph.add_conditional_edges("CUSTOMER", customer_router)


# BOOKING NODE CONDITIONAL
def booking_router(state):
    b = state.get("booking", {})
    if b.get("status") != "success":
        return "END"  # booking failed → stop
    return "FEEDBACK"


graph.add_conditional_edges("BOOKING", booking_router)


# FEEDBACK always leads to RCA
graph.add_edge("FEEDBACK", "RCA")

# RCA → END (NOT back to scheduling!)
graph.add_edge("RCA", "END")


final_graph = graph.compile()
