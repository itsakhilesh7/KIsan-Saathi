"""Unit test for Item 1: .env.example matching Settings keys and defaults."""

from pathlib import Path

from backend.app.core.config import Settings


def parse_env_file(path: Path) -> dict[str, str]:
    """Parses a simple .env file into key-value strings."""
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            entries[key.strip()] = val.strip()
    return entries


def test_env_example_matches_settings():
    """Verify .env.example contains every Settings key and defaults match."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    env_example_path = repo_root / ".env.example"
    assert env_example_path.exists(), ".env.example missing at repo root"

    env_vars = parse_env_file(env_example_path)
    s = Settings()
    fields = Settings.model_fields

    # Check key parity
    settings_keys = set(fields.keys())
    env_keys = set(env_vars.keys())

    missing_in_env = settings_keys - env_keys
    extra_in_env = env_keys - settings_keys
    assert not missing_in_env, f"Keys in Settings but missing in .env.example: {missing_in_env}"
    assert not extra_in_env, f"Keys in .env.example but missing in Settings: {extra_in_env}"

    # Check default value matches
    for key, field_info in fields.items():
        env_val = env_vars[key]
        setting_val = getattr(s, key)

        if isinstance(setting_val, bool):
            expected_bool = env_val.lower() in ("true", "1")
            assert expected_bool == setting_val, f"Default mismatch for {key}: env='{env_val}', setting={setting_val}"
        elif isinstance(setting_val, int):
            assert int(env_val) == setting_val, f"Default mismatch for {key}: env='{env_val}', setting={setting_val}"
        else:
            assert env_val == (setting_val or ""), f"Default mismatch for {key}: env='{env_val}', setting='{setting_val}'"

