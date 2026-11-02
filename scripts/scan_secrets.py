#!/usr/bin/env python3
"""Secret scanner for Kisan Saathi repository.

Scans both the working tree and the entire Git commit history for API keys,
passwords, and credentials before code is pushed to public repositories.

Usage:
    python scripts/scan_secrets.py
    # or via PowerShell:
    ./scripts/scan_secrets.ps1
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Common high-risk patterns for API keys, secrets, tokens
SECRET_PATTERNS = [
    (r"(?i)(?:api_key|apikey|secret|token|password|auth_token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", "Generic High-Entropy Key/Secret"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Access Token"),
    (r"glpat-[a-zA-Z0-9_\-]{20,}", "GitLab Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/LLM Secret Key"),
    (r"EAAB[a-zA-Z0-9]{30,}", "Meta/Facebook User/Page Access Token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "Private Key Header"),
    (r"(?i)ai\.vachana\.ai.*[a-zA-Z0-9]{24,}", "Gnani Secret/Token"),
]

# Patterns or values that are safe false positives (placeholders / test dummies)
ALLOWLIST_VALUES = {
    "change_me",
    "change_me_random_string",
    "change_me_super_secret_phone_salt_kisan_2026",
    "mock_token",
    "mock_token_123",
    "test_key",
    "mock_key",
    "your_openai_or_groq_api_key_here",
    "your_data_gov_in_api_key_here",
    "your_permanent_system_user_token_here",
    "your_meta_app_secret_here",
    "your_gnani_api_key_here",
    "your_db_password",
    "openai-compatible-model",
    "9ef84268-d588-465a-a308-a864a43d0070",  # Public data.gov.in resource ID
}

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "data",
    "logs",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".png",
    ".jpg",
    ".jpeg",
    ".ogg",
    ".wav",
    ".zip",
}


def is_allowed(matched_str: str) -> bool:
    """Checks if matched secret string is an allowable placeholder."""
    cleaned = matched_str.strip().strip("'\"")
    if cleaned in ALLOWLIST_VALUES:
        return True
    lower = cleaned.lower()
    if any(placeholder in lower for placeholder in [
        "change_me", "mock", "dummy", "test", "example", "sample", "secure_", "prod_"
    ]):
        return True
    return False


def scan_working_tree(repo_root: Path) -> list[str]:
    """Scans all files in the working directory for secrets."""
    findings = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            path = Path(root) / f
            if path.suffix in EXCLUDE_EXTENSIONS:
                continue
            if path.name == ".env":
                findings.append(f"[WORKING TREE] Real .env file detected at: {path}")
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, desc in SECRET_PATTERNS:
                for match in re.finditer(pattern, content):
                    matched_val = match.group(1) if match.groups() else match.group(0)
                    if not is_allowed(matched_val):
                        # Mask secret in display
                        masked = matched_val[:4] + "..." + matched_val[-4:] if len(matched_val) > 8 else "***"
                        findings.append(f"[WORKING TREE] {path} matches {desc}: {masked}")
    return findings


def scan_git_history() -> list[str]:
    """Scans git commit history diffs for secrets."""
    findings = []
    try:
        p = subprocess.run(
            ["git", "log", "-p", "--all"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        if p.returncode != 0:
            return [f"git log failed: {p.stderr}"]
    except Exception as e:
        return [f"Could not run git log: {e}"]

    current_commit = "HEAD"
    for line in p.stdout.splitlines():
        if line.startswith("commit "):
            current_commit = line.split()[1][:8]
        elif line.startswith("+") and not line.startswith("+++"):
            added_line = line[1:].strip()
            for pattern, desc in SECRET_PATTERNS:
                for match in re.finditer(pattern, added_line):
                    matched_val = match.group(1) if match.groups() else match.group(0)
                    if not is_allowed(matched_val):
                        masked = matched_val[:4] + "..." + matched_val[-4:] if len(matched_val) > 8 else "***"
                        findings.append(f"[GIT HISTORY] Commit {current_commit} matches {desc}: {masked}")

    return findings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[*] Scanning Kisan Saathi working tree at {repo_root}...")
    wt_findings = scan_working_tree(repo_root)

    print("[*] Scanning Git commit history...")
    git_findings = scan_git_history()

    all_findings = wt_findings + git_findings
    if all_findings:
        print("\n[!] SECRETS DETECTED:")
        for finding in all_findings:
            print(f"  - {finding}")
        print("\n[!] FAILED: Resolve or remove the above credentials before pushing!")
        return 1

    print("\n[OK] CLEAN: No exposed secrets detected in working tree or git history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
