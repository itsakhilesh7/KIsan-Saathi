"""Commodity alias resolver matching farmer terminology to Agmarknet canonical commodity names."""

import logging
import re
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


def _matches_marker(marker: str, text: str) -> bool:
    """Matches a marker using script-safe whole-word or exact-token boundaries."""
    clean_m = marker.strip().lower()
    if not clean_m:
        return False
    if re.search(r"[a-zA-Z]", clean_m) or clean_m.isdigit():
        pattern = r"\b" + r"\s+".join(re.escape(w) for w in clean_m.split()) + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))
    else:
        tokens = [w.strip(".,?!;:'\"()[]{}") for w in text.split() if w.strip(".,?!;:'\"()[]{}")]
        m_tokens = clean_m.split()
        if len(m_tokens) == 1:
            m_tok = m_tokens[0]
            return any(t == m_tok or (len(m_tok) >= 3 and t.startswith(m_tok)) for t in tokens)
        else:
            n = len(m_tokens)
            return any(tokens[i : i + n] == m_tokens for i in range(len(tokens) - n + 1))


def is_ambiguous_chilli(text: str) -> bool:
    """Returns True if user mentions chilli generically without specifying green or dry."""
    if not text:
        return False

    # If already explicitly matches green or dry chilli, it is NOT ambiguous
    has_green = any(_matches_marker(m, text) for m in GREEN_CHILLI_MARKERS)
    has_dry = any(_matches_marker(m, text) for m in DRY_CHILLI_MARKERS)
    if has_green or has_dry:
        return False

    return any(_matches_marker(k, text) for k in AMBIGUOUS_CHILLI_KEYWORDS)


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

    # Alias list match with whole-word / token boundaries
    for canonical, lang_map in aliases.items():
        if isinstance(lang_map, dict):
            for lang, word_list in lang_map.items():
                if isinstance(word_list, list):
                    for alias in word_list:
                        alias_clean = alias.strip().lower()
                        if _matches_marker(alias_clean, word):
                            return canonical

    return None
