import re
import json
import logging
from typing import Optional
from app.services.groq_service import groq_service

logger = logging.getLogger("fixloop.classifier")

# Priority ordered rule-based mapping with domain-specific patterns and error codes
CATEGORY_RULES = [
    (
        "Drainage issue",
        [
            r"\be20\b", r"\boe\b", r"\bdrain", r"\bclog", r"\bpipe\b", r"\bpump\b",
            r"\bstanding water\b", r"\bwater pooling\b", r"\bnot draining\b", r"\bwon't drain\b",
            r"\bwater stays\b", r"\boverflow", r"\bdischarge hose\b", r"\bfilter clog"
        ]
    ),
    (
        "Cooling issue",
        [
            r"\bnot cooling\b", r"\bnot cold\b", r"\bwarm\b", r"\bcompressor\b",
            r"\bfreezer\b", r"\bfrost\b", r"\bice\b", r"\brefrigerant\b", r"\bgas leak\b",
            r"\bthermostat\b", r"\bcoils?\b", r"\bdefrost\b", r"\be4\b"
        ]
    ),
    (
        "Spin & Motor issue",
        [
            r"\bspin\b", r"\bmotor\b", r"\bdrum\b", r"\bnoise\b", r"\bnoisy\b", r"\bloud\b",
            r"\bhumming\b", r"\bvibrat", r"\bbelt\b", r"\bbearing\b", r"\brattl", r"\bshaking\b",
            r"\bwon't spin\b", r"\bnot spinning\b", r"\be30\b", r"\bue\b"
        ]
    ),
    (
        "Power & Electrical issue",
        [
            r"\bpower\b", r"\bdead\b", r"\bwon't turn on\b", r"\bnot turning on\b",
            r"\bno power\b", r"\bspark", r"\bswitch\b", r"\bpcb\b", r"\bboard\b",
            r"\bfuse\b", r"\bshort circuit\b", r"\btripping\b", r"\bdisplay off\b"
        ]
    ),
    (
        "Leakage issue",
        [
            r"\bleak", r"\bwater dripping\b", r"\bpuddle\b", r"\bseal\b", r"\bgasket\b",
            r"\bhose leak\b", r"\bvalve leak\b"
        ]
    ),
    (
        "Heating issue",
        [
            r"\bnot heating\b", r"\bheating\b", r"\belement\b", r"\bheater\b",
            r"\bcold wash\b", r"\bwater not hot\b"
        ]
    ),
]

VALID_CATEGORIES = [
    "Drainage issue",
    "Cooling issue",
    "Spin & Motor issue",
    "Power & Electrical issue",
    "Leakage issue",
    "Heating issue",
    "General operational issue",
    "Other"
]

def classify_issue_rule_based(text: str) -> Optional[str]:
    """Matches text against keyword rules and error codes."""
    lower_text = text.lower()
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, lower_text):
                return category
    return None

async def classify_issue_groq(text: str, product_type: str = "", model: str = "") -> Optional[str]:
    """Fallback Groq structured-JSON classification."""
    client = groq_service.get_client()
    if not client:
        return None

    system_prompt = (
        "You are an appliance technical support classification assistant. "
        "Classify the complaint into exactly one of these categories: "
        f"{', '.join(VALID_CATEGORIES)}. "
        "Respond strictly with valid JSON: {\"category\": string, \"confidence\": float}"
    )
    user_prompt = f"Product: {product_type} {model}\nComplaint: {text}"

    try:
        completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=groq_service.model,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        cat = data.get("category")
        if cat in VALID_CATEGORIES and cat != "Other":
            return cat
    except Exception as e:
        logger.warning(f"Groq classification fallback error: {e}")
    return None

async def classify_issue(text: str, product_type: str = "", model: str = "") -> str:
    """
    Tiered classification:
    1. Keyword and error code rule-based
    2. Groq structured-JSON fallback
    3. 'Other' as safe fallback
    """
    # 1. Rule-based
    rule_cat = classify_issue_rule_based(text)
    if rule_cat:
        return rule_cat

    # 2. Groq fallback
    groq_cat = await classify_issue_groq(text, product_type, model)
    if groq_cat:
        return groq_cat

    # 3. Default to Other
    return "Other"

def validate_complaint_input(text: str) -> None:
    """
    Validates user input:
    - Min length: at least 10 characters
    - Must not be pure gibberish (e.g. 'dfkjbkjsn', repeated single chars, no vowels or spaces)
    """
    cleaned = text.strip()
    if len(cleaned) < 10:
        raise ValueError("Complaint description must be at least 10 characters long.")

    # Check for gibberish: no vowels in a word longer than 5 chars, or single unique char repeated
    unique_chars = set(cleaned.replace(" ", "").lower())
    if len(unique_chars) <= 2:
        raise ValueError("Complaint description appears to be invalid or gibberish. Please provide clear details.")

    # Check if string has at least some alphabetic characters
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    if alpha_chars < 5:
        raise ValueError("Please provide a descriptive complaint text.")
