"""Generates evaluation audio variants for Experiment E1: Robustness of Prisma STT.

Conditions generated from source clips:
1. clean: Baseline normalized 16kHz mono WAV.
2. Additive noise:
   - ffmpeg-generated pink noise at SNR 20, 10, and 5 dB
   - ffmpeg-generated brown noise at SNR 20, 10, and 5 dB
   - ESC-50 real field noises (rain, wind, engine) at SNR 20, 10, and 5 dB (if available/downloadable)
3. Telephone simulation:
   - 8 kHz band-limited G.711 mu-law round-trip
   - 8 kHz band-limited AMR-NB (12.2 kbps) round-trip
4. WhatsApp-style:
   - Opus 24 kbps VOIP mode round-trip

All operations use deterministic seeds and exact RMS scaling.
Audio files are written to backend/data/eval_audio/ (gitignored, never committed).
Manifest is saved to out/eval_audio_manifest.csv.
"""

import argparse
import array
import csv
import math
import os
import re
import subprocess
import urllib.request
import wave
from pathlib import Path
from typing import Any

LANG_CODE_MAP = {
    "telugu": "te-IN",
    "hindi": "hi-IN",
    "hinglish": "hi-IN",  # Explicit mode for Hinglish uses hi-IN
    "english": "en-IN",
}

ESC50_URLS = {
    "rain": "https://raw.githubusercontent.com/karolpiczak/ESC-50/master/audio/5-203739-A-10.wav",
    "wind": "https://raw.githubusercontent.com/karolpiczak/ESC-50/master/audio/5-217186-C-16.wav",
    "engine": "https://raw.githubusercontent.com/karolpiczak/ESC-50/master/audio/5-243783-A-44.wav",
}


def compute_rms(samples: array.array) -> float:
    """Computes Root Mean Square (RMS) of audio sample array."""
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def read_wav_16k_mono(path: str | Path) -> tuple[array.array, int]:
    """Reads a 16kHz 16-bit mono WAV file into an array of signed shorts."""
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        if n_channels != 1 or sampwidth != 2 or framerate != 16000:
            raise ValueError(f"WAV file {path} must be 16kHz 16-bit mono (got {framerate}Hz, {sampwidth*8}bit, {n_channels}ch)")
        raw = wf.readframes(n_frames)
        samples = array.array("h")
        samples.frombytes(raw)
        return samples, framerate


def write_wav_16k_mono(path: str | Path, samples: array.array, framerate: int = 16000) -> None:
    """Writes an array of signed shorts into a 16kHz 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(samples.tobytes())


def download_esc50_noise(noise_dir: Path) -> dict[str, Path]:
    """Downloads sample ESC-50 noise WAVs if not already cached locally."""
    noise_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {}
    for name, url in ESC50_URLS.items():
        dest = noise_dir / f"esc50_{name}.wav"
        if not dest.exists():
            print(f"[*] Downloading ESC-50 {name} noise reference...")
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"[+] Downloaded ESC-50 {name} noise to {dest}")
            except Exception as e:
                print(f"[-] Warning: Failed to download ESC-50 {name} ({e}). Will skip {name}.")
                continue
        if dest.exists():
            downloaded[name] = dest
    return downloaded


def generate_synthetic_noise(noise_type: str, duration_sec: float, seed: int, out_path: Path) -> None:
    """Generates pink or brown noise via FFmpeg anoisesrc filter with deterministic seed."""
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi",
        "-i", f"anoisesrc=d={duration_sec:.3f}:c={noise_type}:r=16000:a=0.5:s={seed}",
        "-ar", "16000", "-ac", "1",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def mix_noise_at_snr(speech: array.array, noise: array.array, snr_db: float) -> array.array:
    """Mixes noise into speech at the exact requested SNR (dB) using RMS scaling."""
    n_samples = len(speech)
    if len(noise) < n_samples:
        # Loop noise if shorter than speech
        repeats = (n_samples // len(noise)) + 1
        noise = (noise * repeats)[:n_samples]
    else:
        noise = noise[:n_samples]

    s_rms = compute_rms(speech)
    n_rms = compute_rms(noise)

    if s_rms == 0 or n_rms == 0:
        return array.array("h", speech)

    target_n_rms = s_rms / (10.0 ** (snr_db / 20.0))
    scale = target_n_rms / n_rms

    mixed = array.array("h")
    for s, n in zip(speech, noise):
        val = int(s + n * scale)
        clamped = max(-32768, min(32767, val))
        mixed.append(clamped)

    return mixed


def simulate_telephone_g711(in_wav: Path, out_wav: Path) -> None:
    """Simulates PSTN telephone line: 8 kHz band-limited, G.711 mu-law encoded and decoded."""
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(in_wav),
        "-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw",
        "-f", "wav", "-",
    ]
    decode_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "wav", "-i", "-",
        "-ar", "16000", "-ac", "1",
        str(out_wav),
    ]
    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    subprocess.run(decode_cmd, stdin=p1.stdout, check=True)
    p1.stdout.close()
    p1.wait()


def simulate_telephone_amrnb(in_wav: Path, out_wav: Path, tmp_dir: Path, clip_id: str) -> None:
    """Simulates mobile cellular telephone: 8 kHz band-limited, AMR-NB 12.2k encoded and decoded."""
    amr_path = tmp_dir / f"{clip_id}_temp.amr"
    encode_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(in_wav),
        "-ar", "8000", "-ac", "1",
        "-c:a", "libopencore_amrnb", "-b:a", "12.2k",
        str(amr_path),
    ]
    subprocess.run(encode_cmd, check=True)

    decode_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(amr_path),
        "-ar", "16000", "-ac", "1",
        str(out_wav),
    ]
    subprocess.run(decode_cmd, check=True)
    if amr_path.exists():
        amr_path.unlink()


def simulate_whatsapp_opus(in_wav: Path, out_wav: Path, tmp_dir: Path, clip_id: str) -> None:
    """Simulates WhatsApp audio round-trip: Opus 24 kbps VOIP application mode."""
    ogg_path = tmp_dir / f"{clip_id}_temp.ogg"
    encode_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(in_wav),
        "-c:a", "libopus", "-b:a", "24k", "-application", "voip", "-vbr", "on",
        str(ogg_path),
    ]
    subprocess.run(encode_cmd, check=True)

    decode_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(ogg_path),
        "-ar", "16000", "-ac", "1",
        str(out_wav),
    ]
    subprocess.run(decode_cmd, check=True)
    if ogg_path.exists():
        ogg_path.unlink()


def find_source_file(clips_dir: Path, clip_id: str, raw_filename: str) -> Path | None:
    """Finds the raw audio file matching clip ID or filename."""
    if not clips_dir.exists():
        return None
    for f in clips_dir.iterdir():
        if f.name.lower() == raw_filename.lower() or f.stem.lower() == raw_filename.lower():
            return f
    # Conventional mapping: TEL-01 -> Telugu_1, HIN-01 -> Hindi_1, HING-01 -> Hinglish_1
    m = re.match(r"(?i)^(TEL|HIN|HING)-0?(\d+)$", clip_id)
    if m:
        prefix_map = {"tel": "telugu", "hin": "hindi", "hing": "hinglish"}
        lang_prefix = prefix_map.get(m.group(1).lower(), m.group(1).lower())
        target = f"{lang_prefix}_{m.group(2)}".lower()
        for f in clips_dir.iterdir():
            if f.name.lower().startswith(target):
                return f
    return None


def build_all_variants(
    transcripts_csv: str = "backend/data/transcripts.csv",
    clips_dir: str = "backend/data/clips",
    out_audio_dir: str = "backend/data/eval_audio",
    manifest_csv: str = "out/eval_audio_manifest.csv",
    include_esc50: bool = True,
    base_seed: int = 42,
) -> list[dict[str, Any]]:
    """Builds all audio variants and writes an audit manifest CSV."""
    clips_path = Path(clips_dir)
    out_dir = Path(out_audio_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    noise_cache_dir = Path("backend/data/noise")

    # Read transcripts manifest
    with open(transcripts_csv, "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        raise ValueError(f"No entries found in {transcripts_csv}")

    # Optionally download ESC-50 noise references
    esc50_noises = download_esc50_noise(noise_cache_dir) if include_esc50 else {}

    manifest_rows: list[dict[str, Any]] = []

    print(f"[*] Beginning audio variant generation for {len(reader)} clips...")
    print(f"[*] Output directory: {out_dir}")

    tmp_work_dir = Path("out/temp_noise_gen")
    tmp_work_dir.mkdir(parents=True, exist_ok=True)

    for idx, row in enumerate(reader):
        clip_id = row.get("clip_id", f"CLIP_{idx+1}")
        lang_raw = row.get("language", "Telugu").strip()
        lang_code = LANG_CODE_MAP.get(lang_raw.lower(), "te-IN")
        reference = row.get("reference_transcript", "").strip() or row.get("reference", "").strip()
        expected_intent = row.get("expected_intent", "").strip()

        src_file = find_source_file(clips_path, clip_id, row.get("file", ""))
        if not src_file:
            print(f"[-] Warning: Audio file for {clip_id} not found in {clips_dir}. Skipping.")
            continue

        print(f"\n[*] Processing [{idx+1}/{len(reader)}] {clip_id} ({src_file.name}, {lang_raw})...")

        # 1. Clean variant (16kHz mono WAV)
        clean_path = out_dir / f"{clip_id}_clean.wav"
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(src_file),
            "-ar", "16000", "-ac", "1",
            str(clean_path),
        ]
        subprocess.run(cmd, check=True)
        speech_samples, framerate = read_wav_16k_mono(clean_path)
        duration_sec = len(speech_samples) / framerate

        manifest_rows.append({
            "clip_id": clip_id,
            "source_file": src_file.name,
            "language": lang_raw,
            "language_code": lang_code,
            "condition": "clean",
            "condition_type": "clean",
            "noise_source": "none",
            "snr_db": "none",
            "audio_path": str(clean_path).replace("\\", "/"),
            "reference_transcript": reference,
            "expected_intent": expected_intent,
        })

        # 2. Additive Noise: Pink & Brown
        for n_type in ("pink", "brown"):
            noise_wav_path = tmp_work_dir / f"{clip_id}_{n_type}.wav"
            seed = base_seed + (idx * 100) + (1 if n_type == "pink" else 2)
            generate_synthetic_noise(n_type, duration_sec, seed, noise_wav_path)
            noise_samples, _ = read_wav_16k_mono(noise_wav_path)

            for snr in (20, 10, 5):
                cond_name = f"noise_{n_type}_snr{snr}"
                out_path = out_dir / f"{clip_id}_{cond_name}.wav"
                mixed = mix_noise_at_snr(speech_samples, noise_samples, snr_db=float(snr))
                write_wav_16k_mono(out_path, mixed, framerate)

                manifest_rows.append({
                    "clip_id": clip_id,
                    "source_file": src_file.name,
                    "language": lang_raw,
                    "language_code": lang_code,
                    "condition": cond_name,
                    "condition_type": "additive_noise",
                    "noise_source": f"ffmpeg_{n_type}",
                    "snr_db": str(snr),
                    "audio_path": str(out_path).replace("\\", "/"),
                    "reference_transcript": reference,
                    "expected_intent": expected_intent,
                })
            if noise_wav_path.exists():
                noise_wav_path.unlink()

        # 3. Additive Noise: ESC-50 Real Field Noises (Rain, Wind, Engine)
        for esc_name, esc_file in esc50_noises.items():
            # Convert ESC-50 reference to 16kHz mono WAV
            esc_16k_path = tmp_work_dir / f"esc16k_{esc_name}.wav"
            if not esc_16k_path.exists():
                subprocess.run([
                    "ffmpeg", "-y", "-v", "error",
                    "-i", str(esc_file),
                    "-ar", "16000", "-ac", "1",
                    str(esc_16k_path),
                ], check=True)
            noise_samples, _ = read_wav_16k_mono(esc_16k_path)

            for snr in (20, 10, 5):
                cond_name = f"noise_{esc_name}_snr{snr}"
                out_path = out_dir / f"{clip_id}_{cond_name}.wav"
                mixed = mix_noise_at_snr(speech_samples, noise_samples, snr_db=float(snr))
                write_wav_16k_mono(out_path, mixed, framerate)

                manifest_rows.append({
                    "clip_id": clip_id,
                    "source_file": src_file.name,
                    "language": lang_raw,
                    "language_code": lang_code,
                    "condition": cond_name,
                    "condition_type": "additive_noise",
                    "noise_source": f"esc50_{esc_name}",
                    "snr_db": str(snr),
                    "audio_path": str(out_path).replace("\\", "/"),
                    "reference_transcript": reference,
                    "expected_intent": expected_intent,
                })

        # 4. Telephone Simulations (G.711 & AMR-NB)
        g711_path = out_dir / f"{clip_id}_tel_g711.wav"
        simulate_telephone_g711(clean_path, g711_path)
        manifest_rows.append({
            "clip_id": clip_id,
            "source_file": src_file.name,
            "language": lang_raw,
            "language_code": lang_code,
            "condition": "tel_g711",
            "condition_type": "telephony",
            "noise_source": "g711_mulaw_8k",
            "snr_db": "none",
            "audio_path": str(g711_path).replace("\\", "/"),
            "reference_transcript": reference,
            "expected_intent": expected_intent,
        })

        amrnb_path = out_dir / f"{clip_id}_tel_amrnb.wav"
        simulate_telephone_amrnb(clean_path, amrnb_path, tmp_work_dir, clip_id)
        manifest_rows.append({
            "clip_id": clip_id,
            "source_file": src_file.name,
            "language": lang_raw,
            "language_code": lang_code,
            "condition": "tel_amrnb",
            "condition_type": "telephony",
            "noise_source": "amr_nb_8k",
            "snr_db": "none",
            "audio_path": str(amrnb_path).replace("\\", "/"),
            "reference_transcript": reference,
            "expected_intent": expected_intent,
        })

        # 5. WhatsApp-style Opus Simulation
        whatsapp_path = out_dir / f"{clip_id}_whatsapp_opus.wav"
        simulate_whatsapp_opus(clean_path, whatsapp_path, tmp_work_dir, clip_id)
        manifest_rows.append({
            "clip_id": clip_id,
            "source_file": src_file.name,
            "language": lang_raw,
            "language_code": lang_code,
            "condition": "whatsapp_opus",
            "condition_type": "whatsapp",
            "noise_source": "opus_24k_voip",
            "snr_db": "none",
            "audio_path": str(whatsapp_path).replace("\\", "/"),
            "reference_transcript": reference,
            "expected_intent": expected_intent,
        })

    # Save manifest CSV
    os.makedirs(os.path.dirname(manifest_csv) or ".", exist_ok=True)
    fieldnames = [
        "clip_id", "source_file", "language", "language_code",
        "condition", "condition_type", "noise_source", "snr_db",
        "audio_path", "reference_transcript", "expected_intent",
    ]
    with open(manifest_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\n[+] SUCCESS: Generated {len(manifest_rows)} audio variants across {len(reader)} clips.")
    print(f"[+] Audio files stored in: {out_dir}")
    print(f"[+] Manifest written to: {manifest_csv}")

    return manifest_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate eval audio variants for Experiment E1.")
    parser.add_argument("--transcripts", default="backend/data/transcripts.csv", help="Transcripts CSV")
    parser.add_argument("--clips-dir", default="backend/data/clips", help="Input clips directory")
    parser.add_argument("--out-dir", default="backend/data/eval_audio", help="Output audio directory")
    parser.add_argument("--manifest", default="out/eval_audio_manifest.csv", help="Manifest output CSV")
    parser.add_argument("--no-esc50", action="store_true", help="Exclude ESC-50 noise downloads")
    args = parser.parse_args()

    build_all_variants(
        transcripts_csv=args.transcripts,
        clips_dir=args.clips_dir,
        out_audio_dir=args.out_dir,
        manifest_csv=args.manifest,
        include_esc50=not args.no_esc50,
    )
