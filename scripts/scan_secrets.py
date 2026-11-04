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
    # Quoted or assigned secrets
    (r"(?i)(?:api_key|apikey|secret|token|password|auth_token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", "Generic Quoted Key/Secret"),
    # Unquoted KEY=VALUE lines
    (r"(?i)^(?:export\s+)?([a-zA-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD)[a-zA-Z0-9_]*)\s*=\s*([a-zA-Z0-9_\-\.]{16,})\s*$", "Unquoted KEY=VALUE Secret"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Access Token"),
    (r"glpat-[a-zA-Z0-9_\-]{20,}", "GitLab Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/LLM Secret Key"),
    (r"EAA[A-Za-z0-9]{20,}", "Meta User/Page/System Token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "Private Key Header"),
]

# Exact placeholder values permitted (no loose substring allowance)
ALLOWLIST_VALUES = {
    "",
    "change_me",
    "change_me_random_string",
    "change_me_super_secret_phone_salt_kisan_2026",
    "mock_token",
    "mock_token_123",
    "test_key",
    "mock_key",
    "mock_audio_media_12345",
    "secure_salt_value_123",
    "secure_token_value_456",
    "prod_secret_123",
    "salt_123",
    "salt_abc",
    "test_meta_app_secret_abc",
    "change_me_to_any_random_string",
    "your_openai_or_groq_api_key_here",
    "your_data_gov_in_api_key_here",
    "your_permanent_system_user_token_here",
    "your_meta_app_secret_here",
    "your_gnani_api_key_here",
    "your_db_password",
    "openai-compatible-model",
    "9ef84268-d588-465a-a308-a864a43d0070",  # Public data.gov.in resource ID
    # Documented placeholder examples
    "your_app_secret_from_app_settings_basic",
    "your_chosen_verify_token",
    "your_temporary_or_system_user_token",
    "your_gnani_api_key_from_app_gnani_ai",
    "choose_a_random_string",
    "your_custom_salt_here",
    "mock_bot_token_12345",
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
    """Checks if matched secret string is an allowable exact placeholder."""
    cleaned = matched_str.strip().strip("'\"")
    return cleaned in ALLOWLIST_VALUES


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
                # Check if file is tracked/staged by Git
                res = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", str(path)],
                    capture_output=True,
                    check=False,
                )
                if res.returncode == 0:
                    findings.append(f"[WORKING TREE] Tracked .env file detected in Git at: {path}")
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, desc in SECRET_PATTERNS:
                for match in re.finditer(pattern, content, flags=re.MULTILINE):
                    # Pick the secret capture group if available
                    matched_val = match.group(2) if len(match.groups()) >= 2 else (match.group(1) if match.groups() else match.group(0))
                    if not is_allowed(matched_val):
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
                    matched_val = match.group(2) if len(match.groups()) >= 2 else (match.group(1) if match.groups() else match.group(0))
                    if not is_allowed(matched_val):
                        masked = matched_val[:4] + "..." + matched_val[-4:] if len(matched_val) > 8 else "***"
                        findings.append(f"[GIT HISTORY] Commit {current_commit} matches {desc}: {masked}")

    return findings


def scan_for_committed_env_files() -> list[str]:
    """Flags any git commit that ever added a real .env file."""
    findings = []
    try:
        p = subprocess.run(
            ["git", "log", "--all", "--diff-filter=A", "--name-only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        if p.returncode != 0:
            return [f"git log for added files failed: {p.stderr}"]

        current_commit = "HEAD"
        for line in p.stdout.splitlines():
            line = line.strip()
            if line.startswith("commit "):
                current_commit = line.split()[1][:8]
            elif line.endswith(".env") and not line.endswith(".env.example"):
                findings.append(f"[GIT HISTORY] Commit {current_commit} added a real .env file: {line}")
    except Exception as e:
        findings.append(f"Could not check git log for added files: {e}")

    return findings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[*] Scanning Kisan Saathi working tree at {repo_root}...")
    wt_findings = scan_working_tree(repo_root)

    print("[*] Scanning Git commit history diffs...")
    git_findings = scan_git_history()

    print("[*] Checking for historically committed .env files...")
    env_findings = scan_for_committed_env_files()

    all_findings = wt_findings + git_findings + env_findings
    if all_findings:
        print("\n[!] SECRETS DETECTED:")
        for finding in all_findings:
            print(f"  - {finding}")
        print("\n[!] FAILED: Resolve or remove the above credentials before pushing!")
        return 1

    print("\n[OK] CLEAN: No exposed secrets or committed .env files detected in working tree or git history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
