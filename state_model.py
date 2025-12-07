from typing import Optional, Dict, Any
from langgraph.graph import MessagesState

class VehicleState(MessagesState):
    vehicle_id: str = ""
    features: Dict[str, Any] = {}
    diagnosis: Dict[str, Any] = {}
    schedule: Dict[str, Any] = {}
    booking: Dict[str, Any] = {}
    feedback: Dict[str, Any] = {}
    insights: Dict[str, Any] = {}
    confirmed: Optional[bool] = None
