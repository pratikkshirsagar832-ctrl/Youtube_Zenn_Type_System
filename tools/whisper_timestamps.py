"""Groq Whisper API wrapper for word-level timing.

Uses Groq's OpenAI-compatible transcription endpoint to extract word-level
timestamps from generated voiceover audio. Piper TTS has no native timestamps,
so we delegate to Groq's hosted Whisper (faster + no local model download).

Endpoint: https://api.groq.com/openai/v1/audio/transcriptions
Model:    whisper-large-v3 (default) — supports word-level timestamp_granularities
Returns:  {"words": [{"word": str, "start": float, "end": float, "confidence": float}]}
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, WHISPER_MODEL, WHISPER_LANGUAGE


DEFAULT_MODEL = "whisper-large-v3"


def _get_client() -> OpenAI:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment (.env)")
    return OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)


def extract_word_timestamps(
    audio_path: str,
    model: str | None = None,
    language: str | None = None,
) -> dict:
    """Extract word-level timestamps from a WAV file using Groq's Whisper API.

    Args:
        audio_path: Path to a WAV / MP3 / M4A / OGG / FLAC / WEBM file.
        model: Groq Whisper model id (default: whisper-large-v3 from config).
        language: ISO-639-1 language code (default: en from config).

    Returns:
        {"words": [{"word": str, "start": float, "end": float, "confidence": float}, ...]}

    Raises:
        FileNotFoundError: audio file missing.
        RuntimeError: GROQ_API_KEY missing or API failure.
    """
    p = Path(audio_path)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    chosen_model = model or WHISPER_MODEL or DEFAULT_MODEL
    chosen_lang = language or WHISPER_LANGUAGE or "en"
    client = _get_client()

    print(f"[whisper] Sending {p.name} to Groq ({chosen_model})...", flush=True)
    with open(p, "rb") as f:
        try:
            resp = client.audio.transcriptions.create(
                file=(p.name, f),
                model=chosen_model,
                language=chosen_lang,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                temperature=0.0,
            )
        except Exception as e:
            raise RuntimeError(f"Groq Whisper API failed: {type(e).__name__}: {e}") from e

    raw_words = []
    if hasattr(resp, "words") and resp.words:
        raw_words = resp.words
    elif isinstance(resp, dict):
        raw_words = resp.get("words", [])

    words: list[dict] = []
    for w in raw_words:
        if isinstance(w, dict):
            word = w.get("word") or w.get("text") or ""
            start = float(w.get("start", 0.0))
            end = float(w.get("end", 0.0))
        else:
            word = getattr(w, "word", "") or getattr(w, "text", "")
            start = float(getattr(w, "start", 0.0))
            end = float(getattr(w, "end", 0.0))
        words.append({
            "word": str(word).strip(),
            "start": start,
            "end": end,
            "confidence": 1.0,
        })

    print(f"[whisper] Extracted {len(words)} words via Groq", flush=True)
    return {"words": words}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m tools.whisper_timestamps <audio.wav>")
        sys.exit(1)
    out = extract_word_timestamps(sys.argv[1])
    print(json.dumps(out, indent=2)[:600])
