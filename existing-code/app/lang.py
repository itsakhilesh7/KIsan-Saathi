"""Tiny language helpers (no external deps)."""

SENTENCE_ENDS = ".?!।\n"


def guess_language(text: str) -> str:
    """Guess a Gnani language code from the script of the text."""
    telugu = sum(1 for c in text if "\u0c00" <= c <= "\u0c7f")
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097f")
    if telugu and telugu >= devanagari:
        return "te-IN"
    if devanagari:
        return "hi-IN"
    return "en-IN"


def shorten(text: str, limit: int) -> str:
    """Trim to <= limit chars, preferring to cut at a sentence boundary."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    best = max(cut.rfind(ch) for ch in SENTENCE_ENDS)
    if best >= limit * 0.5:
        return cut[: best + 1].strip()
    return cut.strip()
