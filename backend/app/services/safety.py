"""Agricultural safety, chemical dose stripping, and guardrails (Phase 4 / rules.md §3).

Invariants:
1. Under ALLOW_CHEMICAL_DETAILS=false (default):
   - Strips chemical brand names, active ingredients, dosages, mixtures, and fertilizer quantities.
   - Instructs the user to check the product label and consult their nearest KVK or call 1551.
2. Refuses conclusive disease diagnosis from short symptom descriptions (Rule 3.1).
3. Answers stay qualitative (timing, method, water saving, labour, mechanisation).
4. Prompt injection defense: untrusted text inside cards or user queries cannot hijack instructions.
"""

from __future__ import annotations

import re

from backend.app.core.messages import get_message
from backend.app.core.safety_keywords import (
    ALL_PROHIBITED_CHEMICAL_TOKENS as PROHIBITED_CHEMICAL_TOKENS,
    DIAGNOSIS_KEYWORDS_EN,
    DOSAGE_PATTERN,
    DOSE_INDICATORS_EN,
    INDIC_CHEMICAL_DOSE_KEYWORDS,
    INDIC_DIAGNOSTIC_KEYWORDS,
    OFF_TOPIC_PATTERNS,
    PROMPT_INJECTION_PATTERNS,
)


def contains_prohibited_chemicals(text: str) -> bool:
    """Checks whether text mentions any banned active ingredients or formulations."""
    text_lower = text.lower()
    return any(token.lower() in text_lower for token in PROHIBITED_CHEMICAL_TOKENS)


def contains_dosage_specifications(text: str) -> bool:
    """Checks whether text contains explicit numeric chemical dosages or application rates."""
    return bool(DOSAGE_PATTERN.search(text))


def is_dose_or_chemical_request(query: str) -> bool:
    """Detects if user is asking for specific pesticide doses, chemical mixtures, or spray rates."""
    q_lower = query.lower()
    if any(ind in q_lower for ind in DOSE_INDICATORS_EN):
        return True
    if any(ind in query for ind in INDIC_CHEMICAL_DOSE_KEYWORDS):
        return True
    return contains_prohibited_chemicals(query)


def is_diagnostic_query(query: str) -> bool:
    """Detects if user is attempting to diagnose disease strictly from a brief symptom description."""
    q_lower = query.lower()
    if any(k in q_lower for k in DIAGNOSIS_KEYWORDS_EN):
        return True
    if any(k in query for k in INDIC_DIAGNOSTIC_KEYWORDS):
        return True
    return False


def is_prompt_injection(text: str) -> bool:
    """Detects attempts to manipulate prompt structure or inject system commands."""
    return any(p.search(text) for p in PROMPT_INJECTION_PATTERNS)


def is_off_topic(query: str) -> bool:
    """Detects non-agricultural off-topic queries (medical, legal, etc.)."""
    return any(p.search(query) for p in OFF_TOPIC_PATTERNS)


def get_label_reminder(language: str = "te-IN") -> str:
    """Returns mandatory localized label check reminder per rules.md §3.4."""
    return get_message("label_reminder", language)


def get_diagnosis_refusal_message(language: str = "te-IN") -> str:
    """Returns localized message refusing disease diagnosis from short descriptions."""
    return get_message("disease_diagnosis_refusal", language)


def get_out_of_scope_crop_message(crop_name: str, language: str = "te-IN") -> str:
    """Returns localized polite disclaimer for unsupported crops (e.g. Chilli, Tomato in v1 advisory)."""
    return get_message("crop_scope_disclaimer", language, crop_name=crop_name)


def strip_chemical_details(text: str, language: str = "te-IN") -> str:
    """Strips chemical names and numeric dosages; attaches mandatory label reminder.

    Under ALLOW_CHEMICAL_DETAILS=false:
    - Replaces prohibited chemical tokens with qualitative descriptors.
    - Removes explicit numeric application rates.
    - Appends the mandatory label reminder.
    """
    cleaned = text

    # Remove dosage numbers + units
    cleaned = DOSAGE_PATTERN.sub("", cleaned)

    # Neutralize prompt injection phrases inside untrusted text
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # Replace prohibited chemicals
    for token in PROHIBITED_CHEMICAL_TOKENS:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        if pattern.search(cleaned):
            replacement = get_message("registered_label_formulations", language)
            cleaned = pattern.sub(replacement, cleaned)

    # Collapse excess whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Append mandatory label reminder if chemical tokens were stripped or present
    reminder = get_label_reminder(language)
    if reminder not in cleaned:
        cleaned = f"{cleaned} {reminder}"

    return cleaned


def validate_composer_output(
    answer: str,
    source_text: str,
    allow_chemical_details: bool = False,
) -> tuple[bool, str]:
    """Post-check verification of LLM composed advisory answer (rules.md §2.6, §3.3, §3.4).

    Returns:
        (True, "") if answer adheres to all invariants.
        (False, reason) if validation fails.
    """
    # 1. Chemical tokens check
    if not allow_chemical_details and contains_prohibited_chemicals(answer):
        return False, "Answer contains prohibited chemical token while ALLOW_CHEMICAL_DETAILS=false"

    # 2. Dosage check
    if not allow_chemical_details and contains_dosage_specifications(answer):
        return False, "Answer contains numeric dosage/application rate while ALLOW_CHEMICAL_DETAILS=false"

    # 3. Numeric hallucination check: any number in answer must appear in source text or be standard metadata (1551, year)
    answer_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", answer)
    source_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", source_text))
    # Universal exempt numbers: 1551 (Kisan Call Centre helpline), year parts (2020, 2021, 21, 22, 2026, 1, 2, 3)
    exempt_numbers = {"1551", "2020", "2021", "21", "22", "2026", "1", "2", "3"}

    for num in answer_numbers:
        if num not in source_numbers and num not in exempt_numbers:
            return False, f"Number '{num}' in answer is absent from retrieved source text"

    return True, ""
