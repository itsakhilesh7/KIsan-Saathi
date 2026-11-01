"""Audio processing service using FFmpeg and FFprobe.

Handles audio validation, 16kHz WAV normalization, OGG/Opus encoding for WhatsApp,
and duration-aware audio chunking (<= 25 s) for Gnani Prisma STT.
All subprocess operations are synchronous and must be executed in threads (asyncio.to_thread).
"""

import glob
import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger("audio_service")


class AudioError(Exception):
    """Raised when audio conversion, probing, or chunking fails."""


def _run_cmd(cmd: list[str]) -> str:
    """Executes a subprocess command, returning stdout or raising AudioError."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise AudioError(
            "ffmpeg/ffprobe binary not found on PATH. Install FFmpeg first (e.g. winget install Gyan.FFmpeg)."
        ) from e

    if p.returncode != 0:
        err_msg = p.stderr[-500:].strip()
        log.error("Command '%s' failed: %s", cmd[0], err_msg)
        raise AudioError(f"{cmd[0]} error (exit {p.returncode}): {err_msg}")

    return p.stdout


def get_duration(file_path: str) -> float:
    """Returns the audio duration in seconds using ffprobe."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        out = _run_cmd(cmd)
        return float(out.strip())
    except ValueError as e:
        raise AudioError(f"Unable to parse duration from ffprobe output: {out}") from e


def to_wav16k(src_path: str, dst_path: str) -> str:
    """Converts any audio file to 16 kHz, mono, 16-bit PCM WAV (Prisma STT format)."""
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", src_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        dst_path,
    ]
    _run_cmd(cmd)
    return dst_path


def wav_to_ogg_opus(src_path: str, dst_path: str) -> str:
    """Encodes WAV to WhatsApp-compatible OGG/Opus voice note format.

    Format specs: mono, 24 kHz, 24 kbps, voip mode (plays with inline mic icon if <= 512 KB).
    """
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", src_path,
        "-ac", "1",
        "-ar", "24000",
        "-c:a", "libopus",
        "-b:a", "24k",
        "-application", "voip",
        dst_path,
    ]
    _run_cmd(cmd)
    return dst_path


def split_wav(src_path: str, seg_seconds: int = 25, out_dir: str | None = None) -> list[str]:
    """Splits a WAV file into fixed-length chunks (<= seg_seconds).

    If audio duration is already <= seg_seconds, returns [src_path].
    """
    duration = get_duration(src_path)
    if duration <= seg_seconds:
        return [src_path]

    target_dir = out_dir or os.path.dirname(src_path)
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    pattern = os.path.join(target_dir, "chunk_%03d.wav")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", src_path,
        "-f", "segment",
        "-segment_time", str(seg_seconds),
        "-c", "copy",
        pattern,
    ]
    _run_cmd(cmd)

    chunks = sorted(glob.glob(os.path.join(target_dir, "chunk_*.wav")))
    return chunks or [src_path]
