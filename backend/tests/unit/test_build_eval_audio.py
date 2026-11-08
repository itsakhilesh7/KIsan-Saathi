"""Unit tests for eval audio generation logic and SNR mixing mathematics."""

import array
import math
from pathlib import Path

from backend.scripts.build_eval_audio import compute_rms, mix_noise_at_snr


def test_compute_rms():
    """Verify compute_rms calculates standard mathematical root mean square."""
    # DC signal at 1000
    samples = array.array("h", [1000] * 100)
    assert abs(compute_rms(samples) - 1000.0) < 1e-6

    # Empty array
    assert compute_rms(array.array("h")) == 0.0


def test_mix_noise_at_snr_exact_decibels():
    """Verify mix_noise_at_snr produces exact requested SNR in dB."""
    # Constant amplitude synthetic signals
    speech = array.array("h", [10000] * 1000)
    noise = array.array("h", [5000] * 1000)

    s_rms = compute_rms(speech)

    for target_snr in (20.0, 10.0, 5.0):
        mixed = mix_noise_at_snr(speech, noise, snr_db=target_snr)
        # Extract noise component by subtracting speech
        noise_component = array.array("h", [m - s for m, s in zip(mixed, speech)])
        n_rms = compute_rms(noise_component)

        measured_snr = 20.0 * math.log10(s_rms / n_rms)
        assert abs(measured_snr - target_snr) < 0.05, f"Expected {target_snr} dB, got {measured_snr:.2f} dB"


def test_eval_audio_manifest_structure():
    """Verify generated eval audio manifest has all required fields and valid rows."""
    manifest_path = Path("out/eval_audio_manifest.csv")
    if not manifest_path.exists():
        return

    import csv
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 190  # 10 clips * 19 conditions
    for row in reader:
        assert row["clip_id"]
        assert row["language"] in ("Telugu", "Hindi", "Hinglish")
        assert row["language_code"] in ("te-IN", "hi-IN")
        assert row["condition"]
        assert row["audio_path"]
        assert Path(row["audio_path"]).exists()

