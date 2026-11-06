"""Generates docs/WORDING_REVIEW.md directly from backend.app.core.messages.

Ensures that documentation never drifts from the Single Source of Truth.
"""

from pathlib import Path

from backend.app.core.messages import MESSAGES, SUPPORTED_LANGUAGES

DOC_PATH = Path("docs/WORDING_REVIEW.md")

HEADER = """# Kisan Saathi Wording Review (User-Facing Messages)

All user-visible responses and prompts in Kisan Saathi are centralized in [`backend/app/core/messages.py`](file:///C:/Users/akhil/.gemini/antigravity/scratch/kisan-saathi/backend/app/core/messages.py).
This document presents the complete catalog of strings across **Telugu (`te-IN`)**, **Hindi (`hi-IN`)**, **English (`en-IN`)**, and **Hinglish (`hi-en`)** for native-speaker linguistic review, natural phrasing, and tone calibration.

> [!NOTE]
> **Single Source of Truth Enforced:** This document is auto-generated directly from `backend/app/core/messages.py` via `backend/scripts/generate_wording_review.py`.
> All changes must be made directly in `messages.py`.

---

## 1. Catalog of User-Facing Messages

| Key | Language | Text | Context / Purpose |
|---|---|---|---|
"""


def generate_markdown() -> str:
    rows = []
    for key, lang_map in sorted(MESSAGES.items()):
        for lang in SUPPORTED_LANGUAGES:
            text = lang_map.get(lang, "")
            # Escape pipes for markdown table
            safe_text = text.replace("|", "\\|").replace("\n", " ").strip()
            rows.append(f"| `{key}` | `{lang}` | `{safe_text}` | Centralized template `{key}` |")

    return HEADER + "\n".join(rows) + "\n"


def main() -> None:
    content = generate_markdown()
    DOC_PATH.write_text(content, encoding="utf-8")
    print(f"Successfully generated {DOC_PATH} with {len(MESSAGES)} keys across {len(SUPPORTED_LANGUAGES)} languages.")


if __name__ == "__main__":
    main()
