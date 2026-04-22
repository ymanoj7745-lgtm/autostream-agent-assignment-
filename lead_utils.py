import re
from typing import Optional

from pydantic import BaseModel


PLATFORMS = ["youtube", "instagram", "tiktok", "linkedin", "facebook", "twitter", "x"]
NAME_BLOCKLIST = {
    "plan",
    "pricing",
    "support",
    "refund",
    "captions",
    "video",
    "videos",
    "pro",
    "basic",
    "autostream",
    "youtube",
    "instagram",
    "tiktok",
    "subscribe",
    "signup",
    "sign",
    "start",
    "trial",
    "try",
    "want",
    "good",
    "sounds",
}


class LeadExtractionOutput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    platform: Optional[str] = None
    selected_plan: Optional[str] = None


LEAD_EXTRACTION_PROMPT = """
Extract lead details from the user's latest message.

Only return fields if they are explicitly present or very clearly implied.
- name: the person's name
- email: a valid email address
- platform: creator platform such as YouTube, Instagram, or TikTok
- selected_plan: Basic or Pro if the user mentions a plan or clearly implies one

If a field is missing, return null for it.
""".strip()


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else None


def extract_platform(text: str) -> Optional[str]:
    lowered = text.lower()
    for platform in PLATFORMS:
        if re.search(rf"\b{re.escape(platform)}\b", lowered):
            if platform == "x":
                return "X"
            return platform.title()
    return None


def extract_plan(text: str) -> Optional[str]:
    lowered = text.lower()
    if "pro plan" in lowered or re.search(r"\bpro\b", lowered):
        return "Pro"
    if "basic plan" in lowered or re.search(r"\bbasic\b", lowered):
        return "Basic"
    return None


def extract_name(text: str) -> Optional[str]:
    cleaned = text.strip()
    cleaned_without_email = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "", cleaned).strip(" ,")
    patterns = [
        r"\bmy name is ([A-Za-z ]{2,50})",
        r"\bi am ([A-Za-z ]{2,50})",
        r"\bthis is ([A-Za-z ]{2,50})",
        r"\bi'm ([A-Za-z ]{2,50})",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned_without_email, re.IGNORECASE)
        if match:
            candidate = _normalize_name(match.group(1))
            if is_plausible_name(candidate):
                return candidate

    if re.fullmatch(r"[A-Za-z ]{2,50}", cleaned_without_email):
        candidate = _normalize_name(cleaned_without_email)
        if is_plausible_name(candidate):
            return candidate

    return None


def _normalize_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.strip().split())


def is_plausible_name(name: Optional[str]) -> bool:
    if not name:
        return False

    parts = name.strip().split()
    if len(parts) == 0 or len(parts) > 4:
        return False

    lowered_parts = {part.lower() for part in parts}
    if lowered_parts & NAME_BLOCKLIST:
        return False

    return all(re.fullmatch(r"[A-Za-z]+", part) for part in parts)


def merge_lead_details(
    state: dict,
    name: Optional[str],
    email: Optional[str],
    platform: Optional[str],
    selected_plan: Optional[str] = None,
) -> None:
    current_name = state.get("name")
    if is_plausible_name(name) and (not is_plausible_name(current_name) or not current_name):
        state["name"] = _normalize_name(name)
    if email and not state.get("email"):
        state["email"] = email
    if platform and not state.get("platform"):
        state["platform"] = "X" if platform.lower() == "x" else platform.title()
    if selected_plan in {"Basic", "Pro"} and not state.get("selected_plan"):
        state["selected_plan"] = selected_plan


def get_missing_fields(state: dict) -> list[str]:
    missing = []
    if not is_plausible_name(state.get("name")):
        missing.append("name")
    if not state.get("email"):
        missing.append("email")
    if not state.get("platform"):
        missing.append("platform")
    return missing


def lead_prompt_for_missing_fields(missing_fields: list[str], selected_plan: Optional[str] = None) -> str:
    plan_text = f" for the {selected_plan} plan" if selected_plan else ""
    prompts = {
        ("name",): f"Great choice{plan_text}. May I have your name?",
        ("email",): "Thanks. What is your email address?",
        ("platform",): "Which creator platform do you use most, like YouTube or Instagram?",
        ("name", "email"): f"Great choice{plan_text}. May I have your name and email address?",
        ("name", "platform"): "May I have your name and creator platform?",
        ("email", "platform"): "Please share your email address and creator platform.",
        ("name", "email", "platform"): f"To get you started{plan_text}, please share your name, email address, and creator platform.",
    }
    return prompts[tuple(missing_fields)]
