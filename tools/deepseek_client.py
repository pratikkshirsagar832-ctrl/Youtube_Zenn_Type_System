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
ENHANCE_SYSTEM = """You are a video production director. The user has provided a raw script.
Your job is to split it into perfectly timed voiceover sections and plan every visual scene.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "title": "<max 70 chars, hook-forward>",
  "description": "<max 500 chars>",
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
      "character_expression": "<neutral|curious|shocked|thinking|sad|confident|scared>",
      "character_position": "<left|center|right>",
      "character_animation": "<idle|walk_in_left|walk_in_right|walk_out_left|point_up>",
      "background": {
        "bg_color": "<hex color like #F5ECD7 or #E8D5B7>",
        "elements": [
          {
            "type": "<rect|circle|text|line|path|polygon|timeline_bar|ground>",
            // Position in percent (0-100) of 1920x1080 canvas
            "x_percent": <number or null>,
            "y_percent": <number or null>,
            "width_percent": <number or null>,
            "height_percent": <number or null>,
            "cx_percent": <number or null>,
            "cy_percent": <number or null>,
            "r_percent": <number or null>,
            "x1_percent": <number or null>,
            "y1_percent": <number or null>,
            "x2_percent": <number or null>,
            "y2_percent": <number or null>,
            "fill": "<hex color or null>",
            "stroke": "<hex color or null>",
            "stroke_width": <number or null>,
            "content": "<text string for text type>",
            "font_size": <number or null>,
            "text_anchor": "<start|middle|end>",
            "fill_percent": <0-100 for timeline_bar>,
            "fill_color": "<hex>",
            "remaining_color": "<hex>",
            "year_label": "<string>",
            "ground_color": "<hex>",
            "border_radius": <number or null>
          }
        ]
      },
      "props": [],  // ARRAY OF PROP NAME STRINGS: ["BrainProp"] or ["SkullProp"] — NEVER objects
      "prop_position": "right_of_character",
      "num_characters": 1,
      "motion_type": "<zoom_in_slow|pan_left|pan_right|static>",
      "subtitle_keyword": "<single most emotionally weighted word>"
    }}
  ]
}

BACKGROUND ELEMENT TYPES (all positions as x_percent/y_percent 0-100):
- "rect": x_percent, y_percent, width_percent, height_percent, fill, stroke, stroke_width, border_radius. Use for walls, windows, signs, panels, doors, frames.
- "circle": cx_percent, cy_percent, r_percent, fill, stroke, stroke_width. Use for sun, decorative dots, spotlight.
- "text": x_percent, y_percent, content (the text), font_size (48-72), text_anchor (start/middle/end). Renders in Patrick Hand font. Use for year labels, signs, chalkboard text, titles, thought bubbles.
- "line": x1_percent, y1_percent, x2_percent, y2_percent, stroke, stroke_width. Use for horizon line, floor line, shelf, tabletop, cross-out.
- "path": d (SVG path string), fill, stroke, stroke_width. Use for complex shapes, mountains, waves, abstract curves.
- "polygon": points (array of {x_percent, y_percent}), fill, stroke, stroke_width. Use for triangles, diamonds, arrows, abstract shapes.
- "timeline_bar": A horizontal progress bar. fill_percent (0-100), fill_color, remaining_color, year_label. Use for historical timelines and progress indicators.
- "ground": y_percent (where ground starts), ground_color. Draws a filled rectangle from y_percent to bottom of screen. Always rendered BELOW other elements.

DESIGN RULES:
1. All positions use percentages (0-100). x_percent=50, y_percent=50 = center of 1920x1080 canvas.
2. bg_color sets the overall page/wall color. Elements layer on top.
3. Use at most 2-3 element types per scene. Keep it simple and legible.
4. For character_solo scenes: use bg_color only, or bg_color + a single line for floor.
5. For character_in_room: rect for wall/background + rect for furniture/desk/window + line for floor.
6. For timeline_scene: timeline_bar element + text for year labels.
7. For character_explaining: ground + maybe a circle for sun, rect for chalkboard with text.
8. For text_focus: bg_color + rect as card + text element with the stat/number.
9. For two_characters: bg_color + ground line + maybe a rect table between them.
10. Always use #1A1A1A for stroke colors. Use warm/earthy fills like #F5ECD7, #E8D5B7, #8B6914, #2F4F4F, #4A6741.
11. Every scene MUST have at minimum: bg_color + at least one element.

EXAMPLE BACKGROUNDS BY SCENE:
- Cave (character_in_room): {"bg_color":"#2F2F2F","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":5,"y_percent":5,"width_percent":90,"height_percent":65,"fill":"#2F2F2F","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"ground","y_percent":70,"ground_color":"#3D2B1F"},{"type":"text","x_percent":50,"y_percent":12,"content":"CAVE","font_size":48,"text_anchor":"middle","fill":"#FFFFFF"}]}
- Office (character_in_room): {"bg_color":"#F5F0E8","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5F0E8"},{"type":"rect","x_percent":60,"y_percent":10,"width_percent":30,"height_percent":40,"fill":"#D4E8F0","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"rect","x_percent":10,"y_percent":55,"width_percent":80,"height_percent":8,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3}]}
- Timeline (timeline_scene): {"bg_color":"#F5ECD7","elements":[{"type":"timeline_bar","fill_percent":65,"fill_color":"#8B4513","remaining_color":"#D4C9A8","year_label":"2024"}]}
- Chalkboard (character_explaining): {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":10,"y_percent":5,"width_percent":80,"height_percent":60,"fill":"#2F4F4F","stroke":"#1A1A1A","stroke_width":3,"border_radius":8},{"type":"text","x_percent":50,"y_percent":25,"content":"THE BRAIN","font_size":64,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3}]}
- Statistic (text_focus): {"bg_color":"#1A1A1A","elements":[{"type":"rect","x_percent":15,"y_percent":25,"width_percent":70,"height_percent":50,"fill":"#F5ECD7","stroke":"#1A1A1A","stroke_width":3,"border_radius":12},{"type":"text","x_percent":50,"y_percent":45,"content":"90%","font_size":96,"text_anchor":"middle"},{"type":"text","x_percent":50,"y_percent":60,"content":"of your decisions","font_size":36,"text_anchor":"middle"}]}
- Outdoor (character_explaining): {"bg_color":"#D4E8F0","elements":[{"type":"circle","cx_percent":80,"cy_percent":15,"r_percent":8,"fill":"#FFD700","stroke":"#1A1A1A","stroke_width":2},{"type":"ground","y_percent":70,"ground_color":"#7CB342"},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3}]}

CRITICAL RULES:
1-10: same as before but BACKGROUND section replaced with dynamic element-based backgrounds.
11. PROPS is an array of STRINGS ONLY. Example: "props": ["BrainProp"] or "props": []. NEVER use objects for props.
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
SCENE_SYSTEM = """You are the Scene Director. Break a script into visual scenes.
Each scene = 1 SVG background + 1 Psyche stick figure character + optional props + subtitles.
All visuals are SVG — NO IMAGE GENERATION.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "total_scenes": <int>,
  "scenes": [
    {{
      "scene_id": 1,
      "voiceover_text": "<exact text from script>",
      "scene_type": "<character_solo|character_with_prop|character_in_room|character_explaining|timeline_scene|text_focus|two_characters>",
      "character_expression": "<neutral|curious|shocked|thinking|sad|confident|scared>",
      "character_position": "<left|center|right>",
      "character_animation": "<idle|walk_in_left|walk_in_right|walk_out_left|point_up>",
      "background": {
        "bg_color": "<hex color>",
        "elements": [
          {{
            "type": "<rect|circle|text|line|path|polygon|timeline_bar|ground>",
            "x_percent": <0-100 or null>,
            "y_percent": <0-100 or null>,
            "width_percent": <0-100 or null>,
            "height_percent": <0-100 or null>,
            "cx_percent": <0-100 or null>,
            "cy_percent": <0-100 or null>,
            "r_percent": <0-100 or null>,
            "x1_percent": <0-100 or null>,
            "y1_percent": <0-100 or null>,
            "x2_percent": <0-100 or null>,
            "y2_percent": <0-100 or null>,
            "fill": "<hex color or null>",
            "stroke": "<hex color or null>",
            "stroke_width": <number or null>,
            "content": "<text>",
            "font_size": <number>,
            "text_anchor": "<start|middle|end>",
            "fill_percent": <0-100>,
            "fill_color": "<hex>",
            "remaining_color": "<hex>",
            "year_label": "<string>",
            "ground_color": "<hex>",
            "border_radius": <number>
          }}
        ]
      },
      "props": [],  // ARRAY OF PROP NAME STRINGS: ["BrainProp"] or ["SkullProp"] — NEVER objects
      "prop_position": "right_of_character",
      "num_characters": 1,
      "motion_type": "<zoom_in_slow|pan_left|pan_right|static>",
      "subtitle_keyword": "<single most emotionally weighted word>"
    }}
  ]
}

BACKGROUND ELEMENT TYPES (all positions as x_percent/y_percent 0-100):
- "rect": x_percent, y_percent, width_percent, height_percent, fill, stroke, stroke_width, border_radius. Use for walls, windows, signs, panels, doors, frames.
- "circle": cx_percent, cy_percent, r_percent, fill, stroke, stroke_width. Use for sun, decorative dots, spotlight.
- "text": x_percent, y_percent, content, font_size (48-72), text_anchor (start/middle/end). Renders in Patrick Hand font. Use for year labels, signs, chalkboard text, titles.
- "line": x1_percent, y1_percent, x2_percent, y2_percent, stroke, stroke_width. Use for horizon line, floor, shelf, tabletop.
- "path": d (SVG path), fill, stroke, stroke_width. Use for mountains, waves, abstract curves.
- "polygon": points (array of {x_percent, y_percent}), fill, stroke, stroke_width. Use for triangles, arrows, diamonds.
- "timeline_bar": fill_percent (0-100), fill_color, remaining_color, year_label. Historical timeline progress.
- "ground": y_percent (where ground starts), ground_color. Fills from y_percent to bottom. Rendered BELOW all other elements.

DESIGN RULES:
1. All positions in percent (0-100). x=50,y=50 = center.
2. bg_color sets overall wall/page color. Elements layer on top.
3. Use 2-4 elements per scene. Keep simple and legible.
4. character_solo: bg_color only, or + a floor line.
5. character_in_room: rect for wall + rect for desk/window/shelf + line for floor.
6. timeline_scene: timeline_bar + text year labels.
7. character_explaining: ground + maybe sun circle + rect chalkboard with text.
8. text_focus: bg_color + rect card + large text element with stat.
9. two_characters: bg_color + ground line + maybe table rect between them.
10. Always use #1A1A1A for strokes. Warm/earthy fills: #F5ECD7, #E8D5B7, #8B6914, #2F4F4F, #4A6741.

EXAMPLE BACKGROUNDS:
- Cave: {"bg_color":"#2F2F2F","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#1A1A1A"},{"type":"rect","x_percent":5,"y_percent":5,"width_percent":90,"height_percent":65,"fill":"#2F2F2F","stroke":"#1A1A1A","stroke_width":3,"border_radius":16},{"type":"ground","y_percent":70,"ground_color":"#3D2B1F"},{"type":"text","x_percent":50,"y_percent":12,"content":"CAVE","font_size":48,"text_anchor":"middle","fill":"#FFFFFF"}]}
- Office: {"bg_color":"#F5F0E8","elements":[{"type":"rect","x_percent":0,"y_percent":0,"width_percent":100,"height_percent":100,"fill":"#F5F0E8"},{"type":"rect","x_percent":60,"y_percent":10,"width_percent":30,"height_percent":40,"fill":"#D4E8F0","stroke":"#1A1A1A","stroke_width":2,"border_radius":4},{"type":"rect","x_percent":10,"y_percent":55,"width_percent":80,"height_percent":8,"fill":"#8B6914","stroke":"#1A1A1A","stroke_width":2},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3}]}
- Timeline: {"bg_color":"#F5ECD7","elements":[{"type":"timeline_bar","fill_percent":65,"fill_color":"#8B4513","remaining_color":"#D4C9A8","year_label":"2024"}]}
- Chalkboard: {"bg_color":"#F5ECD7","elements":[{"type":"rect","x_percent":10,"y_percent":5,"width_percent":80,"height_percent":60,"fill":"#2F4F4F","stroke":"#1A1A1A","stroke_width":3,"border_radius":8},{"type":"text","x_percent":50,"y_percent":25,"content":"THE BRAIN","font_size":64,"text_anchor":"middle","fill":"#FFFFFF"},{"type":"line","x1_percent":0,"y1_percent":75,"x2_percent":100,"y2_percent":75,"stroke":"#1A1A1A","stroke_width":3}]}
- Statistic: {"bg_color":"#1A1A1A","elements":[{"type":"rect","x_percent":15,"y_percent":25,"width_percent":70,"height_percent":50,"fill":"#F5ECD7","stroke":"#1A1A1A","stroke_width":3,"border_radius":12},{"type":"text","x_percent":50,"y_percent":45,"content":"90%","font_size":96,"text_anchor":"middle"},{"type":"text","x_percent":50,"y_percent":60,"content":"of your decisions","font_size":36,"text_anchor":"middle"}]}
- Outdoor: {"bg_color":"#D4E8F0","elements":[{"type":"circle","cx_percent":80,"cy_percent":15,"r_percent":8,"fill":"#FFD700","stroke":"#1A1A1A","stroke_width":2},{"type":"ground","y_percent":70,"ground_color":"#7CB342"},{"type":"line","x1_percent":0,"y1_percent":70,"x2_percent":100,"y2_percent":70,"stroke":"#1A1A1A","stroke_width":3}]}

RULES:
1. Each scene = 1 SVG-rendered visual. A section can have 1-3 scenes.
2. voiceover_text per scene: 1-3 sentences (max 30 words).
3. SCENE TYPES: character_solo for narration, character_with_prop for shocking facts, text_focus for stats, character_explaining for explanations, timeline_scene for historical dates, two_characters for emotional dialogue.
4. BACKGROUND: Use the element system above. Every scene's background MUST have at minimum: bg_color + at least one element.
5. PROPS available: SkullProp, FireProp, BrainProp, ClockProp, HeartProp, QuestionMarkProp, BookProp, MirrorProp, ChainProp. PROPS is an ARRAY OF STRINGS. Example: "props": ["BrainProp"] or "props": []. NEVER use objects — just the prop name string.
6. motion_type: cycle through options, NEVER same motion_type 2 scenes in a row.
7. character_expression must match emotional tone of voiceover.
8. NO DURATION HERE. Set to 0 for now. Real duration set from audio.
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
