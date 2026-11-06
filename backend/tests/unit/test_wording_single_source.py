"""Unit tests asserting Single Source of Truth for user-facing wording.

Enforces:
1. No Telugu or Devanagari character literals in backend/app/services/ or backend/app/channels/.
2. All keys in backend/app/core/messages.py have entries for all 4 supported languages.
3. docs/WORDING_REVIEW.md is consistent with messages.py (no drift).
"""

import re
from pathlib import Path

from backend.app.core.messages import MESSAGES, SUPPORTED_LANGUAGES
from backend.scripts.generate_wording_review import generate_markdown


def test_no_indic_scripts_in_services_and_channels():
    """Asserts that no Telugu or Devanagari string literals exist in services/ or channels/."""
    indic_pattern = re.compile(r"[\u0c00-\u0c7f\u0900-\u097f]")
    base_dir = Path("backend/app")

    scanned_files = []
    violations = []

    for subfolder in ("services", "channels"):
        folder_path = base_dir / subfolder
        for py_file in folder_path.rglob("*.py"):
            scanned_files.append(py_file)
            content = py_file.read_text(encoding="utf-8")
            matches = indic_pattern.findall(content)
            if matches:
                violations.append(f"{py_file}: found {len(matches)} Indic script characters (e.g. {matches[:3]})")

    assert len(scanned_files) > 0, "No files found to scan in services/ or channels/"
    assert not violations, "Indic script literals found outside core/messages.py:\n" + "\n".join(violations)


def test_messages_has_all_supported_languages():
    """Every message key must have translations for te-IN, hi-IN, en-IN, and hi-en."""
    missing = []
    for key, lang_map in MESSAGES.items():
        for lang in SUPPORTED_LANGUAGES:
            if not lang_map.get(lang):
                missing.append(f"Key '{key}' missing translation for '{lang}'")

    assert not missing, "Missing translations in messages.py:\n" + "\n".join(missing)


def test_wording_review_doc_matches_messages():
    """Verifies that docs/WORDING_REVIEW.md is in sync with messages.py."""
    doc_path = Path("docs/WORDING_REVIEW.md")
    assert doc_path.exists(), "docs/WORDING_REVIEW.md does not exist"
    current_doc = doc_path.read_text(encoding="utf-8")
    expected_doc = generate_markdown()
    assert current_doc == expected_doc, "docs/WORDING_REVIEW.md has drifted from messages.py. Run python -m backend.scripts.generate_wording_review"

