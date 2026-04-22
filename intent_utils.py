from typing import Literal

from pydantic import BaseModel


IntentType = Literal["greeting", "inquiry", "high_intent"]

HIGH_INTENT_PHRASES = [
    "sign up",
    "get started",
    "buy",
    "purchase",
    "subscribe",
    "want the pro plan",
    "want pro plan",
    "want to try",
    "i want pro",
    "i want the pro plan",
    "i want to start",
    "this sounds good",
]

GREETING_WORDS = ["hi", "hello", "hey", "good morning", "good evening"]
INQUIRY_HINTS = [
    "price",
    "pricing",
    "plan",
    "plans",
    "feature",
    "support",
    "refund",
    "4k",
    "resolution",
    "captions",
]


class IntentClassifierOutput(BaseModel):
    intent: IntentType


INTENT_CLASSIFIER_PROMPT = """
You are classifying the user's latest message for an AutoStream sales assistant.

Return exactly one intent:
- greeting: casual hello or social opener with no buying signal
- inquiry: product, features, pricing, support, or policy question
- high_intent: clear readiness to sign up, start, buy, or try a plan

If the user sounds ready to move forward with a plan, choose high_intent.
""".strip()


def heuristic_intent(user_message: str) -> IntentType:
    msg = user_message.strip().lower()

    if any(phrase in msg for phrase in HIGH_INTENT_PHRASES):
        return "high_intent"

    if any(word in msg for word in INQUIRY_HINTS):
        return "inquiry"

    if any(msg == word or msg.startswith(f"{word} ") for word in GREETING_WORDS):
        return "greeting"

    return "inquiry"
