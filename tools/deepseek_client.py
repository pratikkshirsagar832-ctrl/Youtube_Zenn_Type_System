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
      "image_prompt": "<60-100 word Flux prompt: subject, setting, lighting, mood, style>",
      "motion_type": "<zoom_in_slow|zoom_out_fast|pan_left|pan_right|fade_in|static>",
      "character_expression": "<default|shocked|thinking|explaining|scared|concerned|knowing>",
      "character_position": "<center|left|right>",
      "background_color_hex": "<#0A0A0F|#1A1A24|#14141C|#08080D>",
      "subtitle_keyword": "<single most emotionally weighted word>"
    }}
  ]
}

CRITICAL RULES:
1. Preserve the user's original content and meaning. DO NOT rewrite the topic.
2. Split into 6-10 sections, each 30-180 seconds of voiceover.
3. Each section's voiceover_text: 1-3 paragraphs, max ~150 words.
4. Scenes: 1-3 per section. Each scene = 1-3 sentences (max 30 words).
5. MOTION TYPES must alternate — no same motion_type in consecutive scenes.
6. CHARACTER EXPRESSIONS must match the emotional tone of the voiceover.
7. BACKGROUND COLORS: cycle through the 4 locked colors.
8. Add '...' and '—' frequently in voiceover_text for natural TTS pauses.
9. Image prompts MUST include: subject + setting + lighting + mood + style.
10. subtitle_keyword: the single word with highest emotional weight per scene.
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
Each scene = 1 image (background) + 1 Psyche character expression + 1 motion.

OUTPUT: Valid JSON only. Start with { and end with }.

The JSON must have EXACTLY these keys:
{
  "total_scenes": <int>,
  "scenes": [
    {{
      "scene_id": 1,
      "voiceover_text": "<exact text from script>",
      "image_prompt": "<60-100 word prompt for Flux: subject, setting, lighting, mood, style. Format: '[subject], [setting], [lighting], [mood], cinematic, dark, high contrast, no text, no watermark'>",
      "motion_type": "<zoom_in_slow|zoom_out_fast|pan_left|pan_right|fade_in|static>",
      "character_expression": "<default|shocked|thinking|explaining|scared|concerned|knowing>",
      "character_position": "<center|left|right>",
      "background_color_hex": "<one of: #0A0A0F | #1A1A24 | #14141C | #08080D>",
      "subtitle_keyword": "<the most important single word to highlight in gold>"
    }}
  ]
}

RULES:
1. Each scene = 1 image. A section can have 1-3 scenes.
2. voiceover_text per scene: 1-3 sentences (max 30 words).
3. image_prompt MUST include: subject + setting + lighting + mood + style.
4. motion_type: cycle through options, NEVER same motion_type 2 scenes in a row.
5. character_expression must match emotional tone of voiceover.
6. background_color_hex: use the 4 locked colors in rotation.
7. subtitle_keyword: the word with highest emotional weight in the scene.
8. NO DURATION HERE. Set to 0 for now. Real duration set in Stage 5 from audio.
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
