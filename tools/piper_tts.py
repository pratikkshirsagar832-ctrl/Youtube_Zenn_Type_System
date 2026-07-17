"""Piper TTS wrapper for local voiceover generation.

Generates a single WAV file from concatenated script sections.
Punctuation is normalized for Piper (em-dash kept, ellipses kept).

Voice: en_US-ryan-high (deep male, calm, philosophical).
Download model from:
  https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/high
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from config import PIPER_MODEL_PATH, PIPER_CONFIG_PATH, PIPER_VOICE_NAME


def _check_model() -> None:
    if not Path(PIPER_MODEL_PATH).exists():
        raise FileNotFoundError(
            f"Piper model not found at {PIPER_MODEL_PATH}\n"
            f"Download from: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ryan/high\n"
            f"Files needed: en_US-ryan-high.onnx + en_US-ryan-high.onnx.json"
        )


def _normalize_for_piper(text: str) -> str:
    """Add natural pause markers for more human-like speech.

    Piper treats '...' as a short pause and '—' as a longer pause.
    Auto-injects pauses between sentences and at natural break points
    to make the voiceover sound more natural and conversational.
    """
    import re
    t = text.strip()
    if not t:
        return t

    # Split into sentence-like units
    sentences = re.split(r'(?<=[.!?])\s+', t)
    result = []
    for i, s in enumerate(sentences):
        s = s.strip()
        if not s:
            continue

        # Check if this sentence already has a pause marker
        has_pause = "..." in s or "—" in s

        if has_pause:
            result.append(s)
        else:
            # Add a pause after most sentences for natural rhythm
            pause = "..." if i % 3 != 0 else "..."
            result.append(s + pause)

    return " ".join(result)


def _get_wav_duration(path: str) -> float:
    try:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return frames / float(rate) if rate else 0.0
    except Exception:
        return 0.0


def generate_voiceover(sections: list[dict], output_path: str) -> dict:
    """Generate a single WAV from concatenated sections.

    Args:
        sections: list of {section_name, voiceover_text, estimated_duration_seconds, ...}
        output_path: full path to output WAV file

    Returns:
        {"audio_path": str, "duration_seconds": float}
    """
    _check_model()

    if not shutil.which("piper"):
        raise RuntimeError(
            "piper CLI not found. Install with: pip install piper-tts\n"
            "Then verify: piper --help"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    full_text = "\n\n".join(_normalize_for_piper(s.get("voiceover_text", "")) for s in sections)
    if not full_text.strip():
        raise ValueError("All sections have empty voiceover_text")

    cmd = [
        "piper",
        "--model", PIPER_MODEL_PATH,
        "--config", PIPER_CONFIG_PATH,
        "--output_file", output_path,
    ]

    print(f"[piper] Generating {len(full_text)} chars with {PIPER_VOICE_NAME}...", flush=True)
    proc = subprocess.run(
        cmd,
        input=full_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not Path(output_path).exists():
        raise RuntimeError(
            f"Piper failed (code {proc.returncode}):\nstderr: {proc.stderr[-1500:]}\n"
            f"stdout: {proc.stdout[-500:]}"
        )

    duration = _get_wav_duration(output_path)
    size_kb = Path(output_path).stat().st_size / 1024
    print(f"[piper] Generated {output_path} ({size_kb:.1f} KB, {duration:.1f}s)", flush=True)
    return {
        "audio_path": output_path,
        "duration_seconds": duration,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tools.piper_tts \"<text to speak>\" [output.wav]")
        sys.exit(1)
    text = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "./test_voiceover.wav"
    result = generate_voiceover(
        sections=[{"section_id": 1, "voiceover_text": text}],
        output_path=out_path,
    )
    print(json.dumps(result, indent=2))
