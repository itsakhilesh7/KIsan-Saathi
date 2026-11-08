"""Unit tests for Experiment E1 runner filtering, batching, and metrics calculation."""

from backend.scripts.run_eval_e1 import (
    CORE_CONDITIONS_HINGLISH,
    CORE_CONDITIONS_INDIC,
    filter_planned_rows,
)


def test_filter_planned_rows_core_minimal():
    """Verify core_minimal filters 10 conditions for Indic and 3 conditions for Hinglish."""
    # Synthetic rows matching manifest format
    mock_rows = []
    # 4 Telugu clips * 19 conditions
    for i in range(1, 5):
        cid = f"TEL-0{i}"
        for cond in (
            CORE_CONDITIONS_INDIC + ["noise_rain_snr20", "noise_wind_snr10", "noise_engine_snr5"]
        ):
            mock_rows.append({"clip_id": cid, "language": "Telugu", "condition": cond})

    # 4 Hindi clips * 19 conditions
    for i in range(1, 5):
        cid = f"HIN-0{i}"
        for cond in (
            CORE_CONDITIONS_INDIC + ["noise_rain_snr20", "noise_wind_snr10", "noise_engine_snr5"]
        ):
            mock_rows.append({"clip_id": cid, "language": "Hindi", "condition": cond})

    # 2 Hinglish clips * 19 conditions
    for i in range(1, 3):
        cid = f"HING-0{i}"
        for cond in (
            CORE_CONDITIONS_INDIC + ["noise_rain_snr20", "noise_wind_snr10", "noise_engine_snr5"]
        ):
            mock_rows.append({"clip_id": cid, "language": "Hinglish", "condition": cond})

    filtered = filter_planned_rows(mock_rows, suite="core_minimal")

    # 4 Telugu * 10 conditions = 40
    # 4 Hindi * 10 conditions = 40
    # 2 Hinglish * 3 conditions = 6
    # Total = 86 rows
    assert len(filtered) == 86

    hinglish_rows = [r for r in filtered if r["language"] == "Hinglish"]
    assert len(hinglish_rows) == 6
    for r in hinglish_rows:
        assert r["condition"] in CORE_CONDITIONS_HINGLISH

    indic_rows = [r for r in filtered if r["language"] in ("Telugu", "Hindi")]
    assert len(indic_rows) == 80
    for r in indic_rows:
        assert r["condition"] in CORE_CONDITIONS_INDIC

