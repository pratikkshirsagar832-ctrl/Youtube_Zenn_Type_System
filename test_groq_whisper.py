"""Smoke test for Groq Whisper integration."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.whisper_timestamps import extract_word_timestamps

audio = Path(__file__).resolve().parent / "projects" / "piper_test.wav"
print(f"Audio: {audio} (exists: {audio.exists()})")

result = extract_word_timestamps(str(audio))
words = result["words"]
print(f"\n=== GROQ WHISPER RESULT ===")
print(f"Words extracted: {len(words)}")
print(f"\nFirst 8 words:")
for w in words[:8]:
    print(f"  '{w['word']}'  {w['start']:.2f}s -> {w['end']:.2f}s")
print(f"\nLast 4 words:")
for w in words[-4:]:
    print(f"  '{w['word']}'  {w['start']:.2f}s -> {w['end']:.2f}s")
total_dur = max(w["end"] for w in words) if words else 0
print(f"\nTotal speech duration: {total_dur:.2f}s")
