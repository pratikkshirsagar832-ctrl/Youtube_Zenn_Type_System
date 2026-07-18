"""Scene slicer: splits edit_decisions scenes into 2-second chunks for rapid visuals.

Each scene gets sliced into ceil(duration / 2) chunks. Each chunk:
- Inherits background, character, props from parent scene
- Shows only subtitle words in its time range
- Gets alternating motion_type (pan/zoom/static cycle)
"""
from __future__ import annotations

import math

CHUNK_DURATION = 2.0  # seconds per chunk

MOTION_CYCLE = [
    "zoom_in_slow",
    "pan_right",
    "static",
    "zoom_out_slow",
    "pan_left",
    "static",
]


def slice_scenes(edit_decisions: dict) -> dict:
    """Split every scene into CHUNK_DURATION-second chunks."""
    total = edit_decisions["total_duration_seconds"]
    audio = edit_decisions["audio"]
    scenes = edit_decisions["scenes"]

    out_scenes = []
    chunk_counter = 0
    motion_idx = 0

    for sc in scenes:
        dur = sc["duration_seconds"]
        num_chunks = max(1, math.ceil(dur / CHUNK_DURATION))
        chunk_dur = dur / num_chunks  # distribute evenly

        parent_bg = sc.get("background", {"bg_color": "#FFFFFF", "elements": []})
        parent_expr = sc.get("character_expression", "neutral")
        parent_pos = sc.get("character_position", "center")
        parent_anim = sc.get("character_animation", "idle")
        parent_props = sc.get("props", [])
        parent_prop_pos = sc.get("prop_position", "right_of_character")
        parent_num_chars = sc.get("num_characters", 1)
        parent_subtitle_keyword = sc.get("subtitle_keyword", "")
        parent_voiceover_text = sc.get("voiceover_text", "")
        parent_words = sc.get("subtitle_words", [])
        parent_start = sc.get("start_time", 0.0)

        for ci in range(num_chunks):
            chunk_start = chunk_dur * ci
            chunk_end = min(chunk_dur * (ci + 1), dur)
            abs_start = parent_start + chunk_start
            abs_end = parent_start + chunk_end

            # Filter subtitle words to this chunk's time window
            chunk_words = []
            for w in parent_words:
                w_start = float(w["start"])
                w_end = float(w["end"])
                # Check if word overlaps this chunk's window
                if w_start < chunk_end and w_end > chunk_start:
                    adjusted = {
                        "word": w["word"],
                        "start": round(max(0.0, w_start - chunk_start), 3),
                        "end": round(min(chunk_dur, w_end - chunk_start), 3),
                        "is_keyword": w.get("is_keyword", False),
                    }
                    chunk_words.append(adjusted)

            # Cycle motion
            motion = MOTION_CYCLE[motion_idx % len(MOTION_CYCLE)]
            motion_idx += 1

            out_scenes.append({
                "scene_id": chunk_counter + 1,
                "start_time": round(abs_start, 3),
                "duration_seconds": round(chunk_dur, 3),
                "end_time": round(abs_end, 3),
                "scene_type": sc.get("scene_type", "character_solo"),
                "character_expression": parent_expr,
                "character_position": parent_pos,
                "character_animation": "idle" if ci > 0 else parent_anim,
                "background": parent_bg,
                "props": parent_props,
                "prop_position": parent_prop_pos,
                "num_characters": parent_num_chars,
                "motion_type": motion,
                "subtitle_keyword": parent_subtitle_keyword,
                "voiceover_text": parent_voiceover_text,
                "subtitle_words": chunk_words,
            })
            chunk_counter += 1

    return {
        "total_duration_seconds": total,
        "audio": audio,
        "scenes": out_scenes,
    }
