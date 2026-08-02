"""Nexus pipeline orchestrator.

Order:
  script mode: 0. Enhance script (V3) → 1. TTS → 2. Whisper → 3. Align → 4. Images → 5. Render
  topic mode:  0. Research (R1) → Script (V3) → Scene Plan → 1. TTS → 2. Whisper → 3. Align → 4. Images → 5. Render
  reference mode: fetch YouTube transcript → same as topic mode (with transcript)

Visuals: Pollinations-generated images, animated by Remotion (Ken Burns).
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from config import PROJECTS_DIR, REMOTION_PROJECT_PATH, REMOTION_COMPOSITION

ProgressCallback = Callable[[str, str, float], None]


@dataclass
class PipelineInput:
    project_id: str
    user_input: str
    mode: str
    niche: str
    duration_minutes: int


def _project_dir(project_id: str) -> Path:
    p = PROJECTS_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    (p / "audio").mkdir(exist_ok=True)
    return p


def _emit(on_progress: ProgressCallback | None, stage: str, message: str, progress: float) -> None:
    print(f"[{stage}] {message} ({progress:.0%})", flush=True)
    if on_progress:
        try:
            on_progress(stage, message, progress)
        except Exception:
            pass


# ============================================================
# STAGE 0 — Script Enhancement (DeepSeek V3, mode="script")
# ============================================================
async def stage_0_enhance_script(inp: PipelineInput, on_progress: ProgressCallback | None) -> tuple[dict, dict]:
    _emit(on_progress, "stage_0_enhance", "Enhancing script with DeepSeek V3", 0.05)
    from tools.deepseek_client import enhance_script
    from validators.pydantic_models import Script, ScenePlan, validate_script_total

    raw = await enhance_script(
        user_script=inp.user_input,
        duration_minutes=inp.duration_minutes,
    )

    script = Script.model_validate(raw)
    validate_script_total(script, inp.duration_minutes)
    scene_plan = ScenePlan.model_validate(raw)

    out_path = _project_dir(inp.project_id)
    (out_path / "script.json").write_text(json.dumps(script.model_dump(), indent=2), encoding="utf-8")
    (out_path / "scene_plan.json").write_text(json.dumps(scene_plan.model_dump(), indent=2), encoding="utf-8")
    _emit(on_progress, "stage_0_enhance", "Script + scene plan complete", 0.10)
    return script.model_dump(), scene_plan.model_dump()


# ============================================================
# STAGE 1 — TTS (Piper)
# ============================================================
async def stage_1_tts(inp: PipelineInput, script: dict, on_progress: ProgressCallback | None) -> dict:
    _emit(on_progress, "stage_1_tts", "Generating voiceover with Piper TTS", 0.15)
    from tools.piper_tts import generate_voiceover

    project_dir = _project_dir(inp.project_id)
    result = await asyncio.to_thread(
        generate_voiceover,
        sections=script["sections"],
        output_path=str(project_dir / "audio" / "voiceover.wav"),
    )

    (project_dir / "asset_manifest.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    _emit(on_progress, "stage_1_tts", f"Voiceover done: {result['duration_seconds']:.1f}s", 0.30)
    return result


# ============================================================
# STAGE 2 — Whisper word timestamps
# ============================================================
async def stage_2_whisper(inp: PipelineInput, tts_result: dict, on_progress: ProgressCallback | None) -> dict:
    _emit(on_progress, "stage_2_whisper", "Extracting word timestamps via Groq Whisper", 0.35)
    from tools.whisper_timestamps import extract_word_timestamps

    audio_path = tts_result["audio_path"]
    word_ts = await asyncio.to_thread(extract_word_timestamps, audio_path)

    project_dir = _project_dir(inp.project_id)
    (project_dir / "word_timestamps.json").write_text(json.dumps(word_ts, indent=2), encoding="utf-8")
    _emit(on_progress, "stage_2_whisper", f"{len(word_ts['words'])} words extracted", 0.45)
    return word_ts


# ============================================================
# STAGE 3 — Align timestamps to scene structure
# ============================================================
async def stage_3_align(inp: PipelineInput, scene_plan: dict, word_ts: dict,
                        tts_result: dict, on_progress: ProgressCallback | None) -> list[dict]:
    _emit(on_progress, "stage_3_align", "Aligning words to scenes", 0.50)
    from tools.scene_aligner import build_aligned_scenes
    from validators.pydantic_models import ScenePlan, validate_scene_durations

    aligned = build_aligned_scenes(
        scene_plan=scene_plan,
        word_timestamps=word_ts,
        total_audio_duration=tts_result["duration_seconds"],
    )

    # Quality gate: every scene must be within the shot-duration contract
    validate_scene_durations(ScenePlan(scenes=aligned, total_scenes=len(aligned)))

    project_dir = _project_dir(inp.project_id)
    (project_dir / "aligned_scenes.json").write_text(json.dumps(aligned, indent=2), encoding="utf-8")
    _emit(on_progress, "stage_3_align", f"{len(aligned)} scenes aligned", 0.58)
    return aligned


# ============================================================
# STAGE 4 — Pollinations scene images
# ============================================================
async def stage_4_images(inp: PipelineInput, aligned_scenes: list[dict],
                         on_progress: ProgressCallback | None) -> list[dict]:
    _emit(on_progress, "stage_4_images", f"Generating {len(aligned_scenes)} images with Pollinations", 0.60)
    from tools.pollinations_image import generate_scene_images

    project_dir = _project_dir(inp.project_id)

    def on_image(done: int, total: int) -> None:
        _emit(on_progress, "stage_4_images", f"Image {done}/{total}", 0.60 + 0.25 * (done / total))

    paths = await generate_scene_images(
        scenes=aligned_scenes,
        output_dir=str(project_dir / "images"),
        slug=inp.project_id,
        on_progress=on_image,
    )
    for scene, path in zip(aligned_scenes, paths):
        scene["image_path"] = path

    (project_dir / "aligned_scenes.json").write_text(json.dumps(aligned_scenes, indent=2), encoding="utf-8")
    _emit(on_progress, "stage_4_images", "Scene images complete", 0.88)
    return aligned_scenes


# ============================================================
# STAGE 5 — Build edit_decisions + Remotion render
# ============================================================
async def stage_5_render(inp: PipelineInput, aligned_scenes: list[dict],
                         tts_result: dict,
                         on_progress: ProgressCallback | None) -> dict:
    _emit(on_progress, "stage_5_render", "Building edit decisions and rendering", 0.90)
    from tools.remotion_render import render_video
    from tools.scene_aligner import build_edit_decisions
    from tools.scene_slicer import slice_scenes
    from validators.pydantic_models import EditDecisions

    edit = build_edit_decisions(
        aligned_scenes,
        "audio/voiceover.wav",
        tts_result["duration_seconds"],
    )

    # Schema gate: edit_decisions must satisfy the Remotion contract
    EditDecisions.model_validate(edit)

    # Slice scenes into 2-second chunks for rapid visual changes
    sliced = slice_scenes(edit)
    print(f"[scene_slicer] {len(edit['scenes'])} scenes → {len(sliced['scenes'])} chunks", flush=True)

    project_dir = _project_dir(inp.project_id)
    (project_dir / "edit_decisions.json").write_text(json.dumps(sliced, indent=2), encoding="utf-8")

    mp4_path = str(project_dir / "final_render.mp4")
    await asyncio.to_thread(
        render_video,
        project_id=inp.project_id,
        edit_decisions=sliced,
        output_path=mp4_path,
    )

    _emit(on_progress, "stage_5_complete", "Render complete", 1.0)
    return {
        "mp4_path": mp4_path,
        "total_duration_seconds": sliced["total_duration_seconds"],
    }


# ============================================================
# TOPIC MODE — Research → Script → Scene Plan
# ============================================================
async def stage_1_research(inp: PipelineInput, on_progress: ProgressCallback | None,
                           reference_transcript: str | None = None) -> dict:
    _emit(on_progress, "stage_1_research", "Researching topic with DeepSeek R1", 0.05)
    from tools.deepseek_client import run_research
    from validators.pydantic_models import ResearchBrief

    raw = await run_research(
        topic=inp.user_input,
        niche=inp.niche,
        reference_transcript=reference_transcript,
    )
    brief = ResearchBrief.model_validate(raw)

    out_path = _project_dir(inp.project_id)
    (out_path / "research_brief.json").write_text(json.dumps(brief.model_dump(), indent=2), encoding="utf-8")
    _emit(on_progress, "stage_1_research", "Research complete", 0.10)
    return brief.model_dump()


async def stage_2_script(inp: PipelineInput, research_brief: dict, on_progress: ProgressCallback | None) -> dict:
    _emit(on_progress, "stage_2_script", "Writing script with DeepSeek V3", 0.15)
    from tools.deepseek_client import write_script
    from validators.pydantic_models import Script, validate_script_total

    raw = await write_script(
        research_brief=research_brief,
        duration_minutes=inp.duration_minutes,
        niche=inp.niche,
    )
    script = Script.model_validate(raw)
    validate_script_total(script, inp.duration_minutes)

    out_path = _project_dir(inp.project_id)
    (out_path / "script.json").write_text(json.dumps(script.model_dump(), indent=2), encoding="utf-8")
    _emit(on_progress, "stage_2_script", "Script complete", 0.20)
    return script.model_dump()


async def stage_3_scenes(inp: PipelineInput, script: dict, on_progress: ProgressCallback | None) -> dict:
    _emit(on_progress, "stage_3_scenes", "Planning scenes with DeepSeek V3", 0.25)
    from tools.deepseek_client import plan_scenes
    from validators.pydantic_models import ScenePlan

    raw = await plan_scenes(script=script)
    scene_plan = ScenePlan.model_validate(raw)

    out_path = _project_dir(inp.project_id)
    (out_path / "scene_plan.json").write_text(json.dumps(scene_plan.model_dump(), indent=2), encoding="utf-8")
    _emit(on_progress, "stage_3_scenes", "Scene plan complete", 0.28)
    return scene_plan.model_dump()


# ============================================================
# Main entry point
# ============================================================
async def run_pipeline(inp: PipelineInput,
                       on_progress: ProgressCallback | None = None) -> dict:
    if inp.mode == "script":
        script, scenes = await stage_0_enhance_script(inp, on_progress)
    else:
        reference_transcript = None
        if inp.mode == "reference":
            _emit(on_progress, "stage_0_transcript", "Fetching reference transcript", 0.03)
            from tools.yt_transcript import fetch_youtube_transcript
            reference_transcript = await asyncio.to_thread(
                fetch_youtube_transcript, inp.user_input
            )
            _emit(on_progress, "stage_0_transcript",
                  f"Transcript fetched ({len(reference_transcript)} chars)", 0.05)

        research = await stage_1_research(inp, on_progress, reference_transcript)
        script = await stage_2_script(inp, research, on_progress)
        scenes = await stage_3_scenes(inp, script, on_progress)

    tts_result = await stage_1_tts(inp, script, on_progress)
    word_ts = await stage_2_whisper(inp, tts_result, on_progress)
    aligned = await stage_3_align(inp, scenes, word_ts, tts_result, on_progress)
    aligned = await stage_4_images(inp, aligned, on_progress)
    final = await stage_5_render(inp, aligned, tts_result, on_progress)
    return final
