"""Scene aligner: maps Whisper word timestamps to scenes using real word alignment.

How it works:
- Script words (concatenated scene voiceover_text) are aligned to the Whisper
  transcription with difflib.SequenceMatcher (no proportion guessing).
- Every transcribed word maps to exactly one scene (contiguous ranges).
- Scene duration = word span, padded to MIN / auto-split to MAX.
- Builds edit_decisions.json for Remotion (visuals are Pollinations images).
"""

from __future__ import annotations

import difflib
import re

from config import PIPELINE_MIN_SHOT_DURATION_S, PIPELINE_MAX_SHOT_DURATION_S


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def _script_word_ranges(scene_plan: dict) -> tuple[list[str], list[int]]:
    """Flatten scene voiceover text into words, tagged with scene index."""
    words: list[str] = []
    scene_of: list[int] = []
    for i, s in enumerate(scene_plan["scenes"]):
        text = str(s.get("voiceover_text", "") or "")
        toks = text.split()
        words.extend(toks)
        scene_of.extend([i] * len(toks))
    return words, scene_of


def _map_script_to_transcript(script_words: list[str], trans_words: list[str]) -> list[int | None]:
    """Return, for each script word index, the matching transcript word index (or None)."""
    a = [_norm(w) for w in script_words]
    b = [_norm(w) for w in trans_words]
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)

    mapped: list[int | None] = [None] * len(a)
    for block in matcher.get_matching_blocks():
        a_start, b_start, size = block
        for k in range(size):
            mapped[a_start + k] = b_start + k
    return mapped


def _scene_transcript_ranges(scene_of: list[int], mapped: list[int | None],
                             num_scenes: int, total_words: int) -> list[tuple[int, int]]:
    """Compute [start, end) transcript index range for each scene.

    Uses mapped transcript indices where available; scenes without any match
    fall back to proportional sharing of the remaining transcript words.
    """
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for s in range(num_scenes):
        # First and last script word of this scene
        idxs = [i for i, sc in enumerate(scene_of) if sc == s]
        if not idxs:
            ranges.append((cursor, cursor))
            continue
        first, last = idxs[0], idxs[-1]

        start = mapped[first]
        if start is None:
            # Walk up to the nearest mapped word before this scene
            for i in range(first - 1, -1, -1):
                if mapped[i] is not None:
                    start = mapped[i] + 1
                    break
            else:
                start = cursor
        start = max(start, cursor)

        end = mapped[last]
        if end is None:
            for i in range(last + 1, len(mapped)):
                if mapped[i] is not None:
                    end = mapped[i]
                    break
            else:
                end = total_words
        end = min(end + 1, total_words)

        if start >= end:
            start, end = cursor, min(cursor + 1, total_words)

        # Make ranges contiguous: a scene cannot start before the previous ended
        start = max(start, cursor)
        end = max(end, start)
        ranges.append((start, end))
        cursor = end

    # Stretch the last scene to consume any remaining words
    if ranges and ranges[-1][1] < total_words:
        s, e = ranges[-1]
        ranges[-1] = (s, total_words)

    return ranges


def _split_by_duration(scene: dict, words: list[dict]) -> list[dict]:
    """Split one scene into <=MAX chunks at word boundaries. Returns list of scenes."""
    dur = max(PIPELINE_MIN_SHOT_DURATION_S,
              words[-1]["end"] - words[0]["start"] if words else PIPELINE_MIN_SHOT_DURATION_S)
    if dur <= PIPELINE_MAX_SHOT_DURATION_S:
        scene["duration_seconds"] = round(dur, 3)
        return [scene]

    n = max(2, round(dur / PIPELINE_MAX_SHOT_DURATION_S))
    target = dur / n
    chunks: list[list[dict]] = [[] for _ in range(n)]
    base_start = words[0]["start"]
    for w in words:
        idx = min(n - 1, int((w["start"] - base_start) / target))
        chunks[idx].append(w)

    out = []
    for ch in chunks:
        if not ch:
            continue
        piece = dict(scene)
        piece["subtitle_words"] = ch
        piece["duration_seconds"] = round(
            max(PIPELINE_MIN_SHOT_DURATION_S, ch[-1]["end"] - ch[0]["start"]), 3
        )
        out.append(piece)
    return out or [scene]


def build_aligned_scenes(scene_plan: dict, word_timestamps: dict,
                         total_audio_duration: float) -> list[dict]:
    """Map Whisper words to scenes via real text alignment. Returns aligned scenes."""
    all_words = word_timestamps.get("words", [])
    if not all_words:
        raise RuntimeError("word_timestamps is empty")

    raw_scenes = scene_plan["scenes"]
    script_words, scene_of = _script_word_ranges(scene_plan)
    mapped = _map_script_to_transcript(script_words, [w.get("word", "") for w in all_words])
    ranges = _scene_transcript_ranges(
        scene_of, mapped, len(raw_scenes), len(all_words)
    )

    aligned: list[dict] = []
    for i, scene in enumerate(raw_scenes):
        start_idx, end_idx = ranges[i]
        scene_words = all_words[start_idx:end_idx]

        if not scene_words:
            scene_words = [all_words[min(start_idx, len(all_words) - 1)]]

        keyword = scene.get("subtitle_keyword", "") or ""
        norm_kw = _norm(keyword)
        subtitle_words = []
        for w in scene_words:
            word = str(w.get("word", ""))
            is_kw = bool(norm_kw) and _norm(word) == norm_kw
            subtitle_words.append({
                "word": word,
                "start": round(float(w["start"]), 3),
                "end": round(float(w["end"]), 3),
                "is_keyword": is_kw,
            })

        first_start = float(scene_words[0]["start"])
        last_end = float(scene_words[-1]["end"])
        duration = max(PIPELINE_MIN_SHOT_DURATION_S, last_end - first_start)

        # Last scene: extend to cover the full audio (capped so the shot
        # duration contract is never violated)
        if i == len(raw_scenes) - 1 and end_idx >= len(all_words):
            gap = total_audio_duration - last_end
            gap = min(gap, max(0.0, PIPELINE_MAX_SHOT_DURATION_S - duration))
            if gap > 0:
                duration += gap

        base = {
            "scene_id": i + 1,
            "duration_seconds": round(duration, 3),
            "transcribed_text": " ".join(str(w.get("word", "")) for w in scene_words),
            "voiceover_text": scene.get("voiceover_text", ""),
            "scene_type": scene.get("scene_type", "character_solo"),
            "character_expression": scene.get("character_expression", "neutral"),
            "character_position": scene.get("character_position", "center"),
            "character_animation": scene.get("character_animation", "idle"),
            "background": scene.get("background", {"bg_color": "#1A1A1A", "elements": []}),
            "props": scene.get("props", []),
            "prop_position": scene.get("prop_position", "right_of_character"),
            "num_characters": scene.get("num_characters", 1),
            "motion_type": scene.get("motion_type", "zoom_in_slow"),
            "subtitle_keyword": keyword,
            "image_path": scene.get("image_path", ""),
            "subtitle_words": subtitle_words,
        }
        aligned.extend(_split_by_duration(base, scene_words))

    # Renumber after splitting
    for n, s in enumerate(aligned):
        s["scene_id"] = n + 1
    return aligned


def build_edit_decisions(aligned_scenes: list[dict],
                         voiceover_path: str, total_audio_duration: float) -> dict:
    """Build final edit_decisions.json for Remotion from aligned scenes."""
    out_scenes = []
    current_time = 0.0
    used_motions: list[str] = []

    for s in aligned_scenes:
        duration = s["duration_seconds"]

        # Motion: cycle to avoid consecutive same
        motion = s.get("motion_type", "zoom_in_slow")
        alt = ["zoom_in_slow", "pan_left", "pan_right", "static"]
        if used_motions and motion == used_motions[-1]:
            idx = alt.index(motion) + 1 if motion in alt else 0
            motion = alt[idx % len(alt)]
        used_motions.append(motion)

        # Adjust word timestamps to be relative to scene start_time
        raw_words = s.get("subtitle_words", [])
        adjusted_words = []
        for w in raw_words:
            adjusted_words.append({
                "word": w["word"],
                "start": round(max(0.0, float(w["start"]) - current_time), 3),
                "end": round(max(0.0, float(w["end"]) - current_time), 3),
                "is_keyword": w.get("is_keyword", False),
            })

        out_scenes.append({
            "scene_id": s["scene_id"],
            "start_time": round(current_time, 3),
            "duration_seconds": round(duration, 3),
            "end_time": round(current_time + duration, 3),
            "image_path": s.get("image_path", ""),
            "scene_type": s.get("scene_type", "character_solo"),
            "character_expression": s.get("character_expression", "neutral"),
            "character_position": s.get("character_position", "center"),
            "character_animation": s.get("character_animation", "idle"),
            "background": s.get("background", {"bg_color": "#1A1A1A", "elements": []}),
            "props": s.get("props", []),
            "prop_position": s.get("prop_position", "right_of_character"),
            "num_characters": s.get("num_characters", 1),
            "motion_type": motion,
            "subtitle_keyword": s.get("subtitle_keyword", ""),
            "voiceover_text": s.get("transcribed_text", ""),
            "subtitle_words": adjusted_words,
        })
        current_time += duration

    total = max(round(current_time, 3), round(total_audio_duration, 3))
    if out_scenes and total > current_time:
        gap = round(total - current_time, 3)
        last = out_scenes[-1]
        gap = min(gap, max(0.0, round(PIPELINE_MAX_SHOT_DURATION_S - last["duration_seconds"], 3)))
        if gap > 0:
            last["duration_seconds"] = round(last["duration_seconds"] + gap, 3)
            last["end_time"] = round(last["end_time"] + gap, 3)
            current_time += gap
            total = round(current_time, 3)

    return {
        "total_duration_seconds": total,
        "audio": {
            "voiceover": voiceover_path,
            "music": "",
            "music_volume": 0.0,
        },
        "scenes": out_scenes,
    }
