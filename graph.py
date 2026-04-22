from pathlib import Path
from typing import Literal
import re
import time

from google import genai
from langgraph.graph import END, StateGraph

from intent_utils import heuristic_intent
from lead_utils import (
    extract_email,
    extract_name,
    extract_platform,
    extract_plan,
    get_missing_fields,
    lead_prompt_for_missing_fields,
    merge_lead_details,
)
from rag_utils import build_vectorstore, retrieve_context
from state import AgentState
from tools import mock_lead_capture


GENERATION_MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]


def build_agent() -> tuple[object, object]:
    client = genai.Client()
    base_dir = Path(__file__).resolve().parent
    vectorstore = build_vectorstore(str(base_dir / "knowledge_base.md"))

    def classify_intent_node(state: AgentState) -> dict:
        message = state["pending_user_message"]
        intent = heuristic_intent(message)

        if not state["lead_captured"] and state.get("intent") == "high_intent":
            return {"intent": "high_intent"}

        return {"intent": intent}

    def greeting_node(state: AgentState) -> dict:
        latest = state["pending_user_message"].lower()
        if any(word in latest for word in ["price", "pricing", "plan", "plans", "4k", "captions", "support", "refund"]):
            context = retrieve_context(vectorstore, state["pending_user_message"])
            answer = _answer_from_context(client, state["pending_user_message"], context)
            return {"retrieved_context": context, "answer": answer}

        return {
            "answer": "Hello! I can help with AutoStream pricing, features, support policies, and getting started with a plan."
        }

    def inquiry_node(state: AgentState) -> dict:
        context = retrieve_context(vectorstore, state["pending_user_message"])
        answer = _answer_from_context(client, state["pending_user_message"], context)
        return {
            "retrieved_context": context,
            "answer": answer,
        }

    def high_intent_node(state: AgentState) -> dict:
        message = state["pending_user_message"]

        extracted_name = extract_name(message)
        extracted_email = extract_email(message)
        extracted_platform = extract_platform(message)
        extracted_plan = extract_plan(message)

        merge_lead_details(state, extracted_name, extracted_email, extracted_platform, extracted_plan)

        missing_fields = get_missing_fields(state)
        if missing_fields:
            return {
                "name": state.get("name"),
                "email": state.get("email"),
                "platform": state.get("platform"),
                "selected_plan": state.get("selected_plan"),
                "answer": lead_prompt_for_missing_fields(missing_fields, state.get("selected_plan")),
            }

        if not state["lead_captured"]:
            result = mock_lead_capture(state["name"], state["email"], state["platform"])
            plan_line = f"Preferred plan: {state['selected_plan']}\n" if state.get("selected_plan") else ""
            return {
                "name": state["name"],
                "email": state["email"],
                "platform": state["platform"],
                "selected_plan": state.get("selected_plan"),
                "lead_captured": True,
                "lead_capture_result": result,
                "answer": (
                    "Lead captured successfully.\n"
                    f"Name: {state['name']}\n"
                    f"Email: {state['email']}\n"
                    f"Platform: {state['platform']}\n"
                    f"{plan_line}"
                    "You're all set. Our team will reach out soon."
                ),
            }

        return {"answer": "Your details are already captured. Our team will contact you soon."}

    def route_intent(state: AgentState) -> Literal["greeting", "inquiry", "high_intent"]:
        return state["intent"] or "inquiry"

    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("greeting", greeting_node)
    graph.add_node("inquiry", inquiry_node)
    graph.add_node("high_intent", high_intent_node)
    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "greeting": "greeting",
            "inquiry": "inquiry",
            "high_intent": "high_intent",
        },
    )
    graph.add_edge("greeting", END)
    graph.add_edge("inquiry", END)
    graph.add_edge("high_intent", END)

    return graph.compile(), client


def _answer_from_context(client: genai.Client, question: str, context: str) -> str:
    try:
        return _generate_text(client, _build_prompt(question, context))
    except Exception:
        return _offline_answer(question, context)


def _build_prompt(question: str, context: str) -> str:
    return (
        "You are answering questions about AutoStream, an automated video editing SaaS for creators.\n\n"
        "Use only the retrieved knowledge base context below.\n"
        "If the answer is not in the context, say that you only know what is available in the local knowledge base.\n"
        "Keep the answer concise, confident, and sales-friendly.\n"
        "When useful, mention the exact plan name and price.\n\n"
        f"Retrieved context:\n{context}\n\n"
        f"Latest user question:\n{question}"
    )


def _generate_text(client: genai.Client, prompt: str) -> str:
    last_error = None
    for model_name in GENERATION_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                return (response.text or "").strip()
            except Exception as exc:
                last_error = exc
                if any(code in str(exc) for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2 + attempt)
                    continue
                break
    if last_error:
        raise last_error
    raise RuntimeError("Gemini generation failed.")


def _offline_answer(question: str, context: str) -> str:
    q = question.lower()
    has_basic = "basic plan" in context.lower()
    has_pro = "pro plan" in context.lower()

    if any(word in q for word in ["pricing", "price", "plans"]) and has_basic and has_pro:
        return (
            "AutoStream offers two plans:\n"
            "- Basic Plan: $29/month, 10 videos/month, 720p resolution\n"
            "- Pro Plan: $79/month, unlimited videos, 4K resolution, AI captions"
        )

    if "4k" in q or "captions" in q:
        return "Yes. The Pro Plan includes 4K resolution and AI captions at $79/month."

    if "refund" in q and "support" in q:
        return "AutoStream does not offer refunds after 7 days, and 24/7 support is available only on the Pro plan."

    if "refund" in q:
        return "AutoStream does not offer refunds after 7 days."

    if "support" in q:
        return "24/7 support is available only on the Pro plan."

    if "basic" in q and has_basic:
        return "The Basic Plan is $29/month and includes 10 videos per month at 720p resolution."

    if "pro" in q and has_pro:
        return "The Pro Plan is $79/month and includes unlimited videos, 4K resolution, and AI captions."

    lines = [line.strip('- ').strip() for line in context.splitlines() if line.strip()]
    if lines:
        summary = lines[:4]
        return "Here is what I found in the local knowledge base:\n- " + "\n- ".join(summary)

    return "I can answer using the local knowledge base, but I could not find enough matching information for that question."

