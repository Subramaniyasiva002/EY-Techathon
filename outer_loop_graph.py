# outer_loop_graph.py
from langgraph.graph import StateGraph
from outer_loop_agents import (
    AggregateDataAgent,
    ForecastingAgent,
    RCAAnalyticsAgent,
    ManufacturingSummaryAgent
)

class OuterLoopState(dict):
    pass

g = StateGraph(OuterLoopState)

g.add_node("AGGREGATE", AggregateDataAgent().run)
g.add_node("FORECAST", ForecastingAgent().run)
g.add_node("RCA", RCAAnalyticsAgent().run)
g.add_node("SUMMARY", ManufacturingSummaryAgent().run)
g.add_node("END", lambda s: s)

g.set_entry_point("AGGREGATE")
g.add_edge("AGGREGATE", "FORECAST")
g.add_edge("FORECAST", "RCA")
g.add_edge("RCA", "SUMMARY")
g.add_edge("SUMMARY", "END")
g.set_finish_point("END")

outer_loop_graph = g.compile()
