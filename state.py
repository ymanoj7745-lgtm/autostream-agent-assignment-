from typing import Annotated, List, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


IntentType = Literal["greeting", "inquiry", "high_intent"]
PlanType = Literal["Basic", "Pro"]


class AgentState(TypedDict):
    messages: Annotated[List[dict], add_messages]
    pending_user_message: str
    intent: Optional[IntentType]
    retrieved_context: str
    answer: str
    name: Optional[str]
    email: Optional[str]
    platform: Optional[str]
    selected_plan: Optional[PlanType]
    lead_captured: bool
    lead_capture_result: Optional[str]


def create_initial_state() -> AgentState:
    return {
        "messages": [],
        "pending_user_message": "",
        "intent": None,
        "retrieved_context": "",
        "answer": "",
        "name": None,
        "email": None,
        "platform": None,
        "selected_plan": None,
        "lead_captured": False,
        "lead_capture_result": None,
    }
