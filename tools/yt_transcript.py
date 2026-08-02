"""YouTube transcript fetcher for reference mode.

Uses yt-dlp to pull English (auto) subtitles without downloading the video.
Returns plain-text transcript (tags/timing stripped).
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path


def _strip_vtt(text: str) -> str:
    """Strip WebVTT markup: header, cue timings, <...> tags."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT":
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s+-->\s+\d{2}", line):
            continue
        if line.startswith("Kind:") or line.startswith("Language:") or line.startswith("NOTE"):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("&nbsp;", " ").replace("&amp;", "&")
        if line:
            lines.append(line)
    return " ".join(lines)


def fetch_youtube_transcript(url: str, language: str = "en") -> str:
    """Download and return the (auto) English transcript of a YouTube video.

    Raises:
        RuntimeError: if the video has no English subtitles or download fails.
    """
    import yt_dlp

    with tempfile.TemporaryDirectory(prefix="nexus_yt_") as tmp:
        opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitleslangs": [language],
            "subtitlesformat": "vtt",
            "outtmpl": str(Path(tmp) / "sub"),
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as e:  # noqa: BLE001 - surface clean error
            raise RuntimeError(f"Failed to fetch YouTube transcript: {type(e).__name__}: {e}") from e

        vtts = sorted(Path(tmp).glob("sub*.vtt"))
        if not vtts:
            raise RuntimeError(
                f"No {language} subtitles found for {url} (auto-captions may be disabled)."
            )
        text = _strip_vtt(vtts[0].read_text(encoding="utf-8", errors="replace"))
        if not text.strip():
            raise RuntimeError(f"Transcript for {url} is empty.")
        return text


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m tools.yt_transcript <youtube-url>")
        sys.exit(1)
    print(fetch_youtube_transcript(sys.argv[1])[:2000])
