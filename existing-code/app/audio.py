"""ffmpeg helpers. All functions are synchronous; call them via asyncio.to_thread."""
import glob
import os
import subprocess


class AudioError(Exception):
    pass


def _run(cmd: list[str]) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise AudioError("ffmpeg/ffprobe not found on PATH. Install ffmpeg first.") from e
    if p.returncode != 0:
        raise AudioError(f"{cmd[0]} failed: {p.stderr[-500:]}")
    return p.stdout


def to_wav16k(src: str, dst: str) -> str:
    """Any audio (e.g. WhatsApp OGG/Opus) -> 16 kHz mono 16-bit WAV."""
    _run(["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", dst])
    return dst


def wav_to_ogg_opus(src: str, dst: str) -> str:
    """WAV -> mono OGG/Opus, the format WhatsApp needs for voice notes."""
    _run([
        "ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", "24000",
        "-c:a", "libopus", "-b:a", "24k", "-application", "voip", dst,
    ])
    return dst


def duration_seconds(path: str) -> float:
    out = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ])
    return float(out.strip())


def split_wav(src: str, out_dir: str, seg_seconds: int) -> list[str]:
    """Split into <= seg_seconds pieces. Naive fixed cuts (may cut mid-word).
    TODO: replace with VAD-based splitting (silero-vad) on a quiet point."""
    if duration_seconds(src) <= seg_seconds:
        return [src]
    pattern = os.path.join(out_dir, "chunk_%03d.wav")
    _run([
        "ffmpeg", "-y", "-i", src, "-f", "segment",
        "-segment_time", str(seg_seconds), "-c", "copy", pattern,
    ])
    return sorted(glob.glob(os.path.join(out_dir, "chunk_*.wav")))
