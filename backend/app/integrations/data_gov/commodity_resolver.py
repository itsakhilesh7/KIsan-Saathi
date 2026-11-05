"""Commodity alias resolver matching farmer terminology to Agmarknet canonical commodity names."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("mandi.commodity_resolver")


@lru_cache(maxsize=1)
def load_commodity_aliases() -> dict[str, Any]:
    """Loads and caches the commodity aliases YAML mapping."""
    potential_paths = [
        Path("config/commodity_aliases.yaml"),
        Path(__file__).resolve().parent.parent.parent.parent.parent / "config" / "commodity_aliases.yaml",
        Path(__file__).resolve().parent.parent.parent.parent / "config" / "commodity_aliases.yaml",
    ]
    path = None
    for p in potential_paths:
        if p.exists():
            path = p
            break

    if not path or not path.exists():
        log.warning("commodity_aliases.yaml not found at any potential path")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("aliases", {})


AMBIGUOUS_CHILLI_KEYWORDS = [
    "మిర్చి", "మిరప", "మిరపకాయ", "మిరప పంట",
    "mirchi", "chilli", "chillies", "chilly",
    "मिर्च", "मिर्ची",
]

GREEN_CHILLI_MARKERS = [
    "పచ్చి", "పచ్చిమిర్చి", "green", "hari", "हरी",
]

DRY_CHILLI_MARKERS = [
    "ఎండు", "ఎండుమిర్చి", "ఎర్ర", "dry", "red", "sukhi", "सूखी", "लाल", "endu", "erra",
]


def is_ambiguous_chilli(text: str) -> bool:
    """Returns True if user mentions chilli generically without specifying green or dry."""
    if not text:
        return False
    lower = text.lower()

    # If already explicitly matches green or dry chilli, it is NOT ambiguous
    has_green = any(m in lower for m in GREEN_CHILLI_MARKERS)
    has_dry = any(m in lower for m in DRY_CHILLI_MARKERS)
    if has_green or has_dry:
        return False

    return any(k in lower for k in AMBIGUOUS_CHILLI_KEYWORDS)


def resolve_commodity(word: str) -> str | None:
    """Matches a spoken or typed commodity word (in Telugu, Hindi, or English)

    to its exact dataset commodity string.
    Returns None if no confirmed alias exists (prevents LLM hallucination).
    """
    if not word or not word.strip():
        return None

    cleaned = word.strip().lower()
    aliases = load_commodity_aliases()

    # Exact key match
    for canonical in aliases.keys():
        if cleaned == canonical.lower():
            return canonical

    # Alias list match
    for canonical, lang_map in aliases.items():
        if isinstance(lang_map, dict):
            for lang, word_list in lang_map.items():
                if isinstance(word_list, list):
                    for alias in word_list:
                        if cleaned == alias.strip().lower() or alias.strip().lower() in cleaned:
                            return canonical

    return None
