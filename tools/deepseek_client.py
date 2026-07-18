"""DeepSeek R1 + V3 client. Uses OpenAI-compatible endpoint.

Three functions:
  - run_research(topic, niche, ...) -> dict  (model: deepseek-reasoner)
  - write_script(research_brief, duration_minutes, ...) -> dict  (model: deepseek-chat)
  - plan_scenes(script, ...) -> dict  (model: deepseek-chat)

Each function:
  1. Builds a strict JSON-only system prompt
  2. Calls DeepSeek with retry (3 attempts)
  3. Returns parsed JSON dict

Pydantic validation is done in pipeline.py after this returns.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL_REASONING,
    DEEPSEEK_MODEL_CHAT,
)


def _client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in .env")
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def _extract_json(text: str) -> dict:
    """Find and parse the first JSON object in the LLM response."""
    text = text.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response: {text[:300]}")
    return json.loads(text[start:end + 1])


def _call(model: str, system: str, user: str, max_tokens: int = 6000, temperature: float = 0.5,
          retries: int = 3) -> dict:
    """Call DeepSeek and return parsed JSON dict. Retries on parse failure."""
    client = _client()
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or ""
            return _extract_json(content)
        except json.JSONDecodeError as e:
            last_err = e
            print(f"[deepseek] attempt {attempt}: JSON parse failed: {e}", flush=True)
        except Exception as e:
            last_err = e
            print(f"[deepseek] attempt {attempt}: {type(e).__name__}: {e}", flush=True)
    raise RuntimeError(f"DeepSeek call failed after {retries} attempts: {last_err}")


# ============================================================
# STAGE 0 — Script Enhancement (for mode="script")
# Takes raw user script, reformats into timed voiceover paragraphs
# + full scene plan in a single call.
# ============================================================
ENHANCE_SYSTEM = """You are a CINEMATIC video production director. The user has provided a raw script.
Your job is to split it into perfectly timed voiceover sections and plan every visual scene with rich SVG backgrounds.

All visuals are SVG — NO IMAGE GENERATION. Make every scene visually striking and detailed.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "title": "<max 70 chars, hook-forward>",
  "description": "<max 1000 chars>",
  "tags": ["<tag 1>", "..." (min 5, max 10)],
  "hook": "<the first 2-3 sentences for the opening, max 200 chars>",
  "sections": [
    {{
      "section_id": 1,
      "section_name": "<short label>",
      "voiceover_text": "<the actual script text for this section>",
      "estimated_duration_seconds": <int, 30-180>
    }}
  ],
  "total_estimated_seconds": <int>,
  "call_to_action": "<final 2-3 sentences, soft close>",
  "scenes": [
    {{
      "scene_id": 1,
      "voiceover_text": "<exact 1-3 sentence chunk from a section>",
      "scene_type": "<character_solo|character_with_prop|character_in_room|character_explaining|timeline_scene|text_focus|two_characters>",
      "character_expression": "<neutral|curious|shocked|thinking|sad|confident|scared|confused>",
      "character_position": "<left|center|right>",
      "character_animation": "<idle|walk_in_left|walk_in_right|walk_out_left|point_up>",
      "background": {
        "bg_color": "<hex color like #F5ECD7 or #1A1A1A or #2F4F4F or #F5F0E8 or #D4E8F0>",
        "elements": [
          {{
            "type": "<rect|circle|text|line|path|polygon|timeline_bar|ground|curve|decoration|dotted|grid>",
            "x_percent": <number>,
            "y_percent": <number>,
            "width_percent": <number>,
            "height_percent": <number>,
            "cx_percent": <number>,
            "cy_percent": <number>,
            "r_percent": <number>,
            "x1_percent": <number>,
            "y1_percent": <number>,
            "x2_percent": <number>,
            "y2_percent": <number>,
            "fill": "<hex color>",
            "stroke": "<hex color>",
            "stroke_width": <number>,
            "content": "<text>",
            "font_size": <number 48-96>,
            "text_anchor": "<start|middle|end>",
            "fill_percent": <0-100>,
            "fill_color": "<hex>",
            "remaining_color": "<hex>",
            "year_label": "<string>",
            "ground_color": "<hex>",
            "border_radius": <number>,
            "opacity": <0.0-1.0>,
            "from_x": <number>,
            "from_y": <number>,
            "to_x": <number>,
            "to_y": <number>,
            "control_x": <number>,
            "control_y": <number>,
            "shape": "<star|cross|zigzag>",
            "rows": <number>,
            "cols": <number>,
            "dot_r": <number>,
            "spacing_x": <number>,
            "spacing_y": <number>
          }}
        ]
      },
      "props": [],  // STRING ARRAY ONLY: ["BrainProp"] or ["SkullProp"] or []. NEVER objects.
      "prop_position": "right_of_character",
      "num_characters": 1,
      "motion_type": "<zoom_in_slow|pan_left|pan_right|static>",
      "subtitle_keyword": "<single most emotionally weighted word>"
    }}
  ]
}

AVAILABLE BACKGROUND ELEMENT TYPES:
- "rect": filled/stroked rectangle. Use for walls, windows, doors, frames, signs, furniture, tables.
- "circle": filled/stroked circle/ellipse. Use for sun, moon, lamps, decorative dots, spotlights.
- "text": text rendered in Patrick Hand font. Use for titles, year labels, signs, stats, chalkboard writing.
- "line": straight/wobbly line. Use for floor lines, horizon, shelves, table edges, borders, dividers.
- "path": custom SVG path string. Use for mountains, waves, abstract shapes, curves.
- "polygon": multi-point shape. Use for arrows, triangles, diamonds, abstract geometric decors.
- "timeline_bar": progress bar with year label. Use for historical timelines.
- "ground": fills from y_percent to bottom of screen. Use for floor, grass, ground.
- "curve": quadratic bezier curve defined by from_x/y, to_x/y, control_x/y. Use for banners, decorative arcs.
- "decoration": decorative shapes. Set shape="star" | "cross" | "zigzag", positioned by cx/cy/r.
- "dotted": dot pattern grid. rows, cols, dot_r, spacing_x/y, x_percent/y_percent as top-left.
- "grid": grid lines pattern. rows, cols, spacing_x/y, x_percent/y_percent as top-left.

DESIGN RULES:
1. Every scene MUST have 3-8 elements minimum. More elements = richer visuals.
2. Vary bg_color between scenes — dark for drama, warm for storytelling, blue for calm, green for nature.
3. Always include: background fill rect + ground/floor line + 2-6 decorative elements.
4. Use text elements font_size 48-96 for titles and key numbers.
5. Add dotted/grid patterns in background at low opacity (0.05-0.15) for texture.
6. Add curve elements for banners, arches, decorative flourishes.
7. Add star/cross decorations at low opacity for visual interest.
8. Color palette: stroke=#1A1A1A. Fills: warm creams (#FFF8F2, #F5ECD7, #E8D5B7), earth (#8B6914, #A0522D), deep (#2F4F4F, #1A1A1A), accent (#FF6B35, #4A6741, #D4E8F0).

EXAMPLE SCENES:
- character_solo: {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#FFF8F2"},{"type":"dotted","x_percent":2,"y_percent":5,"rows":12,"cols":16,"dot_r":0.2,"spacing_x":6,"spacing_y":5,"opacity":0.08},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3}]}
- character_in_room (cave): {"bg_color":"#2F2F2F","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":5,"y_percent":5,"width_percent":90,"height_percent":60,"fill":"#2F2F2F","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"ground","y_percent":65,"ground_color":"#3D2B1F"},{"type":"text","x_percent":50,"y_percent":10,"content":"CAVE","font_size":48,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"decoration","cx_percent":15,"cy_percent":20,"r_percent":1.5,"fill":"#FFFFFF","opacity":0.15,"shape":"star"},{"type":"decoration","cx_percent":85,"cy_percent":25,"r_percent":1,"fill":"#FFFFFF","opacity":0.1,"shape":"star"}]}
- character_in_room (office): {"bg_color":"#F5F0E8","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5F0E8"},{"type":"dotted","x_percent":3,"y_percent":3,"rows":10,"cols":15,"dot_r":0.15,"spacing_x":6,"spacing_y":6,"opacity":0.06},{"type":"rect","x_percent":65,"y_percent":8,"width_percent":28,"height_percent":35,"fill":"#D4E8F0","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"rect","x_percent":10,"y_percent":52,"width_percent":80,"height_percent":6,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3}]}
- timeline_scene: {"bg_color":"#F5ECD7","elements":[{"type":"dotted","x_percent":0,"y_percent":0,"rows":8,"cols":12,"dot_r":0.2,"spacing_x":8,"spacing_y":8,"opacity":0.05},{"type":"timeline_bar","fill_percent":42,"fill_color":"#8B4513","remaining_color":"#D4C9A8","year_label":"1957"},{"type":"text","x_percent":50,"y_percent":65,"content":"Timeline","font_size":48,"text_anchor":"middle"}]}
- character_explaining (chalkboard): {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5ECD7"},{"type":"dotted","x_percent":2,"y_percent":2,"rows":6,"cols":10,"dot_r":0.2,"spacing_x":9,"spacing_y":9,"opacity":0.08},{"type":"rect","x_percent":12,"y_percent":5,"width_percent":76,"height_percent":55,"fill":"#2F4F4F","stroke":"#1A1A1A","stroke_width":3,"border_radius":8},{"type":"text","x_percent":50,"y_percent":20,"content":"THE AMYGDALA","font_size":56,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"text","x_percent":50,"y_percent":35,"content":"\"Fear Center\"","font_size":40,"text_anchor":"middle","fill":"#E8D5B7"},{"type":"line","x1_percent":0,"y1_percent":72,"x2_percent":100,"y2_percent":72,"stroke":"#1A1A1A","stroke_width":3}]}
- text_focus (stat): {"bg_color":"#1A1A1A","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":12,"y_percent":18,"width_percent":76,"height_percent":64,"fill":"#FFF8F2","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"text","x_percent":50,"y_percent":42,"content":"90%","font_size":120,"text_anchor":"middle"},{"type":"text","x_percent":50,"y_percent":60,"content":"of decisions are subconscious","font_size":40,"text_anchor":"middle"},{"type":"decoration","cx_percent":30,"cy_percent":35,"r_percent":2,"fill":"#1A1A1A","opacity":0.1,"shape":"star"},{"type":"decoration","cx_percent":70,"cy_percent":35,"r_percent":2,"fill":"#1A1A1A","opacity":0.1,"shape":"star"}]}
- two_characters: {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5ECD7"},{"type":"grid","x_percent":0,"y_percent":0,"rows":8,"cols":12,"spacing_x":8,"spacing_y":7,"opacity":0.04},{"type":"rect","x_percent":30,"y_percent":55,"width_percent":40,"height_percent":10,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3}]}
- outdoor: {"bg_color":"#D4E8F0","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#D4E8F0"},{"type":"circle","cx_percent":82,"cy_percent":14,"r_percent":7,"fill":"#FFD700","stroke":"#1A1A1A","stroke_width":2},{"type":"ground","y_percent":68,"ground_color":"#7CB342"},{"type":"line","x1_percent":0,"y1_percent":68,"x2_percent":100,"y2_percent":68,"stroke":"#1A1A1A","stroke_width":3},{"type":"curve","from_x":10,"from_y":40,"to_x":40,"to_y":40,"control_x":25,"control_y":25,"stroke":"#4A6741","stroke_width":2,"opacity":0.3}]}

CRITICAL RULES:
1. Each scene = 1 rich SVG illustration. Always include 4-8 background elements.
2. PROPS is STRING ARRAY ONLY: ["BrainProp"] or []. NEVER objects.
3. motion_type: cycle, never repeat 2 in a row.
4. character_expression must match emotional tone.
"""


async def enhance_script(user_script: str, duration_minutes: int,
                         system_prompt_override: str | None = None) -> dict:
    """One-call enhancement: raw user script → structured script + full scene plan."""
    system = system_prompt_override or ENHANCE_SYSTEM
    target = duration_minutes * 60
    user = (
        f"Raw script:\n{user_script}\n\n"
        f"Target duration: {duration_minutes} minutes ({target}s)\n\n"
        "Produce the enhanced script + scene plan JSON now."
    )
    return _call(
        model=DEEPSEEK_MODEL_CHAT,
        system=system,
        user=user,
        max_tokens=8000,
        temperature=0.5,
    )


# ============================================================
# STAGE 1 — Research (R1)
# ============================================================
RESEARCH_SYSTEM = """You are the Research Director for a dark-psychology YouTube channel
targeting US audiences (age 20-60, all genders). Produce a research brief that will be
used to write an 8-minute cinematic documentary.

OUTPUT: Valid JSON only. No prose. No markdown. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "topic": "<the topic>",
  "niche": "<dark_psychology|human_behavior>",
  "hook_angles": ["<angle 1>", "<angle 2>", "<angle 3>"],
  "key_facts": ["<real fact 1 with year>", "..." (min 10, max 20)],
  "psychological_trigger": "<curiosity|awe|anxiety|wonder|fear|recognition>",
  "target_emotion": "<primary emotion the viewer will feel>",
  "chosen_angle": "<the best of the 3 hook angles + 1 sentence why>",
  "supporting_research": [{"author": "Name", "year": 2000, "finding": "1 sentence"}],
  "tension": "<the core contradiction or paradox that drives the video>"
}

RULES:
- Every fact MUST be real and citable. Include researcher name + year.
- Hook angles must lead with present-tense sensory moment.
- No round numbers — use specific figures.
- The "tension" is the engine of the video. Find the contradiction.
- 3 hook angles must be DIFFERENT approaches.
- "chosen_angle" maximizes the psychological_trigger.
"""


async def run_research(topic: str, niche: str,
                       reference_transcript: str | None = None,
                       system_prompt_override: str | None = None) -> dict:
    """Run research with DeepSeek R1 (reasoning model)."""
    user = f"Topic: {topic}\nNiche: {niche}\n"
    if reference_transcript:
        user += f"\nReference YouTube transcript:\n{reference_transcript[:4000]}\n"
    user += "\nProduce the research_brief JSON now."
    return _call(
        model=DEEPSEEK_MODEL_REASONING,
        system=system_prompt_override or RESEARCH_SYSTEM,
        user=user,
        max_tokens=4000,
        temperature=0.4,
    )


# ============================================================
# STAGE 2 — Script (V3)
# ============================================================
SCRIPT_SYSTEM = """You are the Script Director for a dark-psychology YouTube channel
targeting US audiences (age 20-60). Write a {duration_minutes}-minute cinematic
script in the style of @Zenn0009 — deep, calm, philosophical, high-retention.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "title": "<max 70 chars, hook-forward, no clickbait>",
  "description": "<max 500 chars, 1-2 paragraphs>",
  "tags": ["<tag 1>", "..." (min 10, max 15)],
  "hook": "<the first 2-3 sentences, max 200 chars, present-tense sensory moment>",
  "sections": [
    {{
      "section_id": 1,
      "section_name": "<short label>",
      "voiceover_text": "<the actual script>",
      "estimated_duration_seconds": <int, 30-180>
    }}
    // min 6, max 10 sections
  ],
  "total_estimated_seconds": <int, within ±30 of {target_seconds}>,
  "call_to_action": "<the last 2-3 sentences, soft tease of next video>"
}

CRITICAL RULES:
1. Voiceover MUST use ellipses (...) and em-dashes (—) FREQUENTLY. These force
   Piper TTS to pause and sound human. Example: "For 300,000 years... humans
   had no light after sunset. But here's what's fascinating — they didn't even
   have candles for most of that time."

2. Every claim cites real research (researcher + year). NEVER invent studies.

3. Word count: 1000-1200 for 7-8 min, 800-1000 for 5-6 min. (Piper ~150 wpm.)

4. Vary sentence length (burstiness). Short punchy + long flowing.

5. Include 6+ re-hook phrases: "But here's what's fascinating...", "And then
   something happened...", "But what she found changed everything...",
   "But here's the part nobody talks about.", "Truth number X...",
   "And here is the part almost nobody quotes."

6. End with a philosophical reframe that echoes the opening hook.
   NO "smash subscribe". Soft, philosophical, next-video tease.

7. Use 1st person (I, we) and 2nd person (you) heavily. Conversational tone.

8. NO bullet points. NO emojis. NO ALL CAPS. NO exclamation marks (use ...).

9. Hook (first 2-3 sentences) MUST contain a present-tense sensory moment.

10. Each section's estimated_duration_seconds must be 30-180.

11. total_estimated_seconds = sum of section durations, within ±30 of {target_seconds}.
"""


async def write_script(research_brief: dict, duration_minutes: int, niche: str,
                       system_prompt_override: str | None = None) -> dict:
    """Write a {duration_minutes}-minute script with DeepSeek V3."""
    target = duration_minutes * 60
    system = (system_prompt_override or SCRIPT_SYSTEM)
    system = system.replace("{duration_minutes}", str(duration_minutes))
    system = system.replace("{target_seconds}", str(target))
    user = (
        f"Research brief:\n{json.dumps(research_brief, indent=2)}\n\n"
        f"Niche: {niche}\nDuration: {duration_minutes} minutes (target {target}s)\n\n"
        "Produce the script JSON now."
    )
    return _call(
        model=DEEPSEEK_MODEL_CHAT,
        system=system,
        user=user,
        max_tokens=6000,
        temperature=0.7,
    )


# ============================================================
# STAGE 3 — Scene Plan (V3)
# ============================================================
SCENE_SYSTEM = """You are a CINEMATIC Scene Director for a Zenn-style explainer video.
Each scene is a hand-drawn SVG illustration with a stick figure character and rich background.
All visuals are SVG — NO IMAGE GENERATION. Make every scene visually striking and detailed.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "total_scenes": <int>,
  "scenes": [
    {{
      "scene_id": 1,
      "voiceover_text": "<exact 1-3 sentences from script>",
      "scene_type": "<character_solo|character_with_prop|character_in_room|character_explaining|timeline_scene|text_focus|two_characters>",
      "character_expression": "<neutral|curious|shocked|thinking|sad|confident|scared|confused>",
      "character_position": "<left|center|right>",
      "character_animation": "<idle|walk_in_left|walk_in_right|walk_out_left|point_up>",
      "background": {
        "bg_color": "<hex color like #F5ECD7 or #1A1A1A or #2F4F4F or #F5F0E8 or #D4E8F0>",
        "elements": [
          {{
            "type": "<rect|circle|text|line|path|polygon|timeline_bar|ground|curve|decoration|dotted|grid>",
            "x_percent": <number>,
            "y_percent": <number>,
            "width_percent": <number>,
            "height_percent": <number>,
            "cx_percent": <number>,
            "cy_percent": <number>,
            "r_percent": <number>,
            "x1_percent": <number>,
            "y1_percent": <number>,
            "x2_percent": <number>,
            "y2_percent": <number>,
            "fill": "<hex color>",
            "stroke": "<hex color>",
            "stroke_width": <number>,
            "content": "<text>",
            "font_size": <number 48-96>,
            "text_anchor": "<start|middle|end>",
            "fill_percent": <0-100>,
            "fill_color": "<hex>",
            "remaining_color": "<hex>",
            "year_label": "<string>",
            "ground_color": "<hex>",
            "border_radius": <number>,
            "opacity": <0.0-1.0>,
            "from_x": <number>,
            "from_y": <number>,
            "to_x": <number>,
            "to_y": <number>,
            "control_x": <number>,
            "control_y": <number>,
            "shape": "<star|cross|zigzag>",
            "rows": <number>,
            "cols": <number>,
            "dot_r": <number>,
            "spacing_x": <number>,
            "spacing_y": <number>
          }}
        ]
      },
      "props": [],  // STRING ARRAY ONLY: ["BrainProp"] or ["SkullProp"] or []. NEVER objects.
      "prop_position": "right_of_character",
      "num_characters": 1,
      "motion_type": "<zoom_in_slow|pan_left|pan_right|static>",
      "subtitle_keyword": "<single most emotionally weighted word>"
    }}
  ]
}

AVAILABLE BACKGROUND ELEMENT TYPES (all positions as x_percent/y_percent 0-100 of 1920x1080 canvas):
- "rect": filled/stroked rectangle. Use for walls, windows, doors, frames, signs, furniture, tables.
- "circle": filled/stroked circle/ellipse. Use for sun, moon, lamps, decorative dots, spotlights.
- "text": text rendered in Patrick Hand font. Use for titles, year labels, signs, stats, chalkboard writing, labels.
- "line": straight/wobbly line. Use for floor lines, horizon, shelves, table edges, borders, dividers.
- "path": custom SVG path string. Use for mountains, waves, abstract shapes, curves.
- "polygon": multi-point shape. Use for arrows, triangles, diamonds, abstract geometric decors.
- "timeline_bar": progress bar with year label. Use for historical timelines.
- "ground": fills from y_percent to bottom of screen. Use for floor, grass, ground.
- "curve": quadratic bezier curve defined by from_x/y, to_x/y, control_x/y. Use for banners, decorative arcs.
- "decoration": decorative shapes. Set shape="star" | "cross" | "zigzag", positioned by cx/cy/r.
- "dotted": dot pattern grid. rows, cols, dot_r, spacing_x/y, x_percent/y_percent as top-left.
- "grid": grid lines pattern. rows, cols, spacing_x/y, x_percent/y_percent as top-left.

DESIGN RULES:
1. Every scene MUST have 3-8 elements minimum. More elements = richer visuals.
2. Vary bg_color between scenes — dark (#1A1A1A, #2F2F2F) for dramatic moments, warm (#F5ECD7, #E8D5B7) for storytelling, blue (#D4E8F0) for calm, green (#4A6741) for nature.
3. Always add at least: background wall rect (full screen fill), a floor or ground line, decorative elements.
4. Use text elements with font_size 48-96 for titles and key numbers.
5. Add decorative dotted patterns or grid lines in background at low opacity (0.05-0.15) for texture.
6. Add curve elements for banners, arches, decorative flourishes.
7. Add star/cross decorations at low opacity for visual interest.
8. Color palette: stroke=#1A1A1A always. Fills: warm creams (#FFF8F2, #F5ECD7, #E8D5B7), earth (#8B6914, #A0522D), deep (#2F4F4F, #1A1A1A), accent (#FF6B35, #4A6741, #D4E8F0).

EXAMPLE SCENE BY TYPE:
- character_solo in dark room: {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#FFF8F2"},{"type":"dotted","x_percent":2,"y_percent":5,"rows":12,"cols":16,"dot_r":0.2,"spacing_x":6,"spacing_y":5,"opacity":0.08},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3}]}
- character_in_room (cave): {"bg_color":"#2F2F2F","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":5,"y_percent":5,"width_percent":90,"height_percent":60,"fill":"#2F2F2F","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"ground","y_percent":65,"ground_color":"#3D2B1F"},{"type":"text","x_percent":50,"y_percent":10,"content":"CAVE","font_size":48,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"decoration","cx_percent":15,"cy_percent":20,"r_percent":1.5,"fill":"#FFFFFF","opacity":0.15,"shape":"star"},{"type":"decoration","cx_percent":85,"cy_percent":25,"r_percent":1,"fill":"#FFFFFF","opacity":0.1,"shape":"star"}]}
- character_in_room (office): {"bg_color":"#F5F0E8","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5F0E8"},{"type":"dotted","x_percent":3,"y_percent":3,"rows":10,"cols":15,"dot_r":0.15,"spacing_x":6,"spacing_y":6,"opacity":0.06},{"type":"rect","x_percent":65,"y_percent":8,"width_percent":28,"height_percent":35,"fill":"#D4E8F0","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"line","x1_percent":60,"y1_percent":25,"x2_percent":60,"y2_percent":38,"stroke":"#1A1A1A","stroke_width":2},{"type":"rect","x_percent":10,"y_percent":52,"width_percent":80,"height_percent":6,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3},{"type":"curve","from_x":80,"from_y":50,"to_x":95,"to_y":50,"control_x":87,"control_y":35,"stroke":"#1A1A1A","stroke_width":2,"opacity":0.3}]}
- timeline_scene: {"bg_color":"#F5ECD7","elements":[{"type":"dotted","x_percent":0,"y_percent":0,"rows":8,"cols":12,"dot_r":0.2,"spacing_x":8,"spacing_y":8,"opacity":0.05},{"type":"timeline_bar","fill_percent":42,"fill_color":"#8B4513","remaining_color":"#D4C9A8","year_label":"1957"},{"type":"text","x_percent":50,"y_percent":65,"content":"Timeline","font_size":48,"text_anchor":"middle"}]}
- character_explaining (chalkboard): {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5ECD7"},{"type":"dotted","x_percent":2,"y_percent":2,"rows":6,"cols":10,"dot_r":0.2,"spacing_x":9,"spacing_y":9,"opacity":0.08},{"type":"rect","x_percent":12,"y_percent":5,"width_percent":76,"height_percent":55,"fill":"#2F4F4F","stroke":"#1A1A1A","stroke_width":3,"border_radius":8},{"type":"text","x_percent":50,"y_percent":20,"content":"THE AMYGDALA","font_size":56,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"text","x_percent":50,"y_percent":35,"content":"\"Fear Center\"","font_size":40,"text_anchor":"middle","fill":"#E8D5B7"},{"type":"line","x1_percent":0,"y1_percent":72,"x2_percent":100,"y2_percent":72,"stroke":"#1A1A1A","stroke_width":3},{"type":"ground","y_percent":72,"ground_color":"#3D2B1F"}]}
- text_focus (stat): {"bg_color":"#1A1A1A","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":12,"y_percent":18,"width_percent":76,"height_percent":64,"fill":"#FFF8F2","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"text","x_percent":50,"y_percent":42,"content":"90%","font_size":120,"text_anchor":"middle"},{"type":"text","x_percent":50,"y_percent":60,"content":"of decisions are subconscious","font_size":40,"text_anchor":"middle"},{"type":"decoration","cx_percent":30,"cy_percent":35,"r_percent":2,"fill":"#1A1A1A","opacity":0.1,"shape":"star"},{"type":"decoration","cx_percent":70,"cy_percent":35,"r_percent":2,"fill":"#1A1A1A","opacity":0.1,"shape":"star"}]}
- two_characters: {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5ECD7"},{"type":"grid","x_percent":0,"y_percent":0,"rows":8,"cols":12,"spacing_x":8,"spacing_y":7,"opacity":0.04},{"type":"rect","x_percent":30,"y_percent":55,"width_percent":40,"height_percent":10,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3},{"type":"curve","from_x":10,"from_y":30,"to_x":90,"to_y":30,"control_x":50,"control_y":15,"stroke":"#1A1A1A","stroke_width":1.5,"opacity":0.15}]}
- outdoor: {"bg_color":"#D4E8F0","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#D4E8F0"},{"type":"circle","cx_percent":82,"cy_percent":14,"r_percent":7,"fill":"#FFD700","stroke":"#1A1A1A","stroke_width":2},{"type":"ground","y_percent":68,"ground_color":"#7CB342"},{"type":"line","x1_percent":0,"y1_percent":68,"x2_percent":100,"y2_percent":68,"stroke":"#1A1A1A","stroke_width":3},{"type":"curve","from_x":10,"from_y":40,"to_x":40,"to_y":40,"control_x":25,"control_y":25,"stroke":"#4A6741","stroke_width":2,"opacity":0.3},{"type":"decoration","cx_percent":50,"cy_percent":50,"r_percent":1,"fill":"#1A1A1A","opacity":0.08,"shape":"star"}]}

CINEMATIC RULES:
1. Each scene = 1 rich SVG illustration. Always include 4-8 background elements for visual richness.
2. voiceover_text: exactly from script, 1-3 sentences max.
3. SCENE TYPES: character_solo (narration, use dotted background), character_with_prop (shocking facts, use prop), text_focus (stats, large text), character_explaining (chalkboard/teaching), timeline_scene (timeline_bar), two_characters (emotional dialogue), character_in_room (rich room environment).
4. BACKGROUND: MUST include: background fill rect + ground or floor line + 2-6 decorative elements (dotted, grid, curves, decorations). Rich, layered, visually interesting.
5. PROPS: ["SkullProp"] ["FireProp"] ["BrainProp"] ["ClockProp"] ["HeartProp"] ["QuestionMarkProp"] ["BookProp"] ["MirrorProp"] ["ChainProp"] — STRINGS ONLY in array.
6. motion_type: cycle, never repeat 2 in a row.
7. character_expression must match emotional tone.
8. NO DURATION — set 0, real duration from audio.
"""


async def plan_scenes(script: dict, system_prompt_override: str | None = None) -> dict:
    """Generate the scene plan with DeepSeek V3."""
    system = system_prompt_override or SCENE_SYSTEM
    user = (
        f"Script:\n{json.dumps(script, indent=2)}\n\n"
        "Produce the scene_plan JSON now."
    )
    return _call(
        model=DEEPSEEK_MODEL_CHAT,
        system=system,
        user=user,
        max_tokens=8000,
        temperature=0.5,
    )
