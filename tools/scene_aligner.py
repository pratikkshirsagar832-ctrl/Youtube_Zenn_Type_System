"""Scene aligner: maps Whisper word timestamps to scenes proportionally.

Key behaviors:
- Words are assigned to scenes proportionally by voiceover_text length
- Every word maps to exactly one scene (no gaps)
- Scene duration = last word end - first word start
- Last scene extended to cover full audio duration
- Builds edit_decisions.json for Remotion (no image_map needed — all SVG)
"""

from __future__ import annotations

import re
from pathlib import Path

from config import (
    PIPELINE_MIN_SHOT_DURATION_S,
    PIPELINE_MAX_SHOT_DURATION_S,
)


def build_aligned_scenes(scene_plan: dict, word_timestamps: dict,
                         total_audio_duration: float) -> list[dict]:
    """Map words to scenes proportionally. Every word assigned. Returns aligned scenes."""
    all_words = word_timestamps.get("words", [])
    if not all_words:
        raise RuntimeError("word_timestamps is empty")

    raw_scenes = scene_plan["scenes"]
    total_words = len(all_words)

    # Calculate proportional word counts per scene based on voiceover_text length
    text_lengths = [len(s.get("voiceover_text", "")) for s in raw_scenes]
    total_len = sum(text_lengths) or 1

    # Assign word ranges to each scene
    aligned = []
    cursor = 0
    for i, scene in enumerate(raw_scenes):
        # Proportional word count for this scene
        proportion = text_lengths[i] / total_len
        scene_word_count = max(1, round(proportion * total_words))

        # Clamp to remaining words on last scene
        if i == len(raw_scenes) - 1:
            scene_word_count = total_words - cursor

        start_idx = cursor
        end_idx = min(cursor + scene_word_count - 1, total_words - 1)
        cursor = end_idx + 1

        # Get actual transcribed words for this scene
        scene_words = all_words[start_idx:end_idx + 1]

        # Build subtitle_words
        keyword = scene.get("subtitle_keyword", "") or ""
        subtitle_words = []
        for w in scene_words:
            word = w.get("word", "")
            is_kw = word.lower().strip(".,!?;:") == keyword.lower().strip(".,!?;:")
            subtitle_words.append({
                "word": word,
                "start": round(float(w["start"]), 3),
                "end": round(float(w["end"]), 3),
                "is_keyword": is_kw,
            })

        # Duration = word span, clamped
        first_start = float(scene_words[0]["start"]) if scene_words else 0.0
        last_end = float(scene_words[-1]["end"]) if scene_words else PIPELINE_MIN_SHOT_DURATION_S
        duration = max(PIPELINE_MIN_SHOT_DURATION_S, last_end - first_start)

        # Last scene: extend to cover full audio
        if i == len(raw_scenes) - 1 and cursor >= total_words:
            audio_gap = total_audio_duration - last_end
            if audio_gap > 0:
                duration += audio_gap

        duration = min(duration, PIPELINE_MAX_SHOT_DURATION_S * 2)

        # Get the actual transcribed text (what Whisper heard)
        transcribed_text = " ".join(w.get("word", "") for w in scene_words)

        aligned.append({
            "scene_id": i + 1,
            "duration_seconds": round(duration, 3),
            "transcribed_text": transcribed_text,
            "voiceover_text": scene.get("voiceover_text", ""),
            "scene_type": scene.get("scene_type", "character_solo"),
            "character_expression": scene.get("character_expression", "neutral"),
            "character_position": scene.get("character_position", "center"),
            "character_animation": scene.get("character_animation", "idle"),
            "background": scene.get("background", {"bg_color": "#FFFFFF", "elements": []}),
            "props": scene.get("props", []),
            "prop_position": scene.get("prop_position", "right_of_character"),
            "num_characters": scene.get("num_characters", 1),
            "motion_type": scene.get("motion_type", "zoom_in_slow"),
            "subtitle_keyword": keyword,
            "subtitle_words": subtitle_words,
        })

    return aligned


def build_edit_decisions(aligned_scenes: list[dict],
                         voiceover_path: str, total_audio_duration: float) -> dict:
    """Build final edit_decisions.json for Remotion from aligned scenes.
    No image_map needed — all visuals are SVG rendered by Remotion."""
    out_scenes = []
    current_time = 0.0
    used_motions: list[str] = []

    for s in aligned_scenes:
        duration = s["duration_seconds"]

        # Motion: cycle to avoid consecutive same
        motion = s.get("motion_type", "zoom_in_slow")
        if used_motions and motion == used_motions[-1]:
            idx = 0
            alt = ["zoom_in_slow", "pan_left", "pan_right", "static"]
            if motion in alt:
                idx = (alt.index(motion) + 1) % len(alt)
                motion = alt[idx]
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
            "scene_type": s.get("scene_type", "character_solo"),
            "character_expression": s.get("character_expression", "neutral"),
            "character_position": s.get("character_position", "center"),
            "character_animation": s.get("character_animation", "idle"),
            "background": s.get("background", {"bg_color": "#FFFFFF", "elements": []}),
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
        last["duration_seconds"] = round(last["duration_seconds"] + gap, 3)
        last["end_time"] = round(last["end_time"] + gap, 3)

    return {
        "total_duration_seconds": total,
        "audio": {
            "voiceover": voiceover_path,
            "music": "",
            "music_volume": 0.0,
        },
        "scenes": out_scenes,
    }
