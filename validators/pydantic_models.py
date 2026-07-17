"""Pydantic models for all 5 Nexus schemas.

Mirrors the JSON schemas in /schemas/. Use these for runtime validation of
LLM outputs.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

from config import (
    MotionType,
    CharacterExpression,
    CharacterPosition,
    BACKGROUND_COLORS,
    VALID_NICHES,
    PIPELINE_MIN_SHOT_DURATION_S,
    PIPELINE_MAX_SHOT_DURATION_S,
)


# ============================================================
# STAGE 1 — Research Brief
# ============================================================
class SupportingResearch(BaseModel):
    author: str
    year: int = Field(ge=1800, le=2030)
    finding: str


class ResearchBrief(BaseModel):
    topic: str
    niche: Literal["dark_psychology", "human_behavior"]
    hook_angles: list[str] = Field(min_length=3, max_length=3)
    key_facts: list[str] = Field(min_length=10, max_length=20)
    psychological_trigger: Literal["curiosity", "awe", "anxiety", "wonder", "fear", "recognition"]
    target_emotion: str
    chosen_angle: str
    supporting_research: list[SupportingResearch]
    tension: str


# ============================================================
# STAGE 2 — Script
# ============================================================
class ScriptSection(BaseModel):
    section_id: int = Field(ge=1)
    section_name: str
    voiceover_text: str = Field(min_length=5)
    estimated_duration_seconds: int = Field(ge=5, le=300)


class Script(BaseModel):
    title: str = Field(max_length=70)
    description: str = Field(max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    hook: str = Field(default="", max_length=500)
    sections: list[ScriptSection] = Field(min_length=1, max_length=30)
    total_estimated_seconds: int = Field(ge=10, le=600)
    call_to_action: str = Field(default="")


def validate_script_total(script: Script, duration_minutes: int) -> None:
    """Extra script-level validation (called separately from model_validate)."""
    target = duration_minutes * 60
    if abs(script.total_estimated_seconds - target) > 30:
        raise ValueError(
            f"total_estimated_seconds ({script.total_estimated_seconds}) is outside ±30s of target ({target})"
        )
    full_text = " ".join(s.voiceover_text for s in script.sections)
    pause_count = full_text.count("...") + full_text.count("—")
    if pause_count < 3:
        raise ValueError(
            f"Only {pause_count} Piper pause markers (... or —) found. Need at least 3."
        )


# ============================================================
# STAGE 3 — Scene Plan
# ============================================================
class Scene(BaseModel):
    scene_id: int = Field(ge=1)
    voiceover_text: str
    image_prompt: str = Field(default="")
    motion_type: str = Field(default="zoom_in_slow")
    character_expression: str = Field(default="default")
    character_position: str = Field(default="center")
    background_color_hex: str = Field(default="#0A0A0F")
    subtitle_keyword: str = Field(default="")
    duration_seconds: float = Field(ge=0.0, default=0.0)


class ScenePlan(BaseModel):
    total_scenes: int = Field(ge=1, default=0)
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def set_total(self) -> "ScenePlan":
        if not self.total_scenes:
            self.total_scenes = len(self.scenes)
        return self


def validate_scene_durations(scene_plan: ScenePlan) -> None:
    """Called AFTER Whisper timestamps to verify real durations are within bounds."""
    for s in scene_plan.scenes:
        if s.duration_seconds < PIPELINE_MIN_SHOT_DURATION_S:
            raise ValueError(
                f"Scene {s.scene_id} duration {s.duration_seconds}s is below MIN "
                f"{PIPELINE_MIN_SHOT_DURATION_S}s. Should have been auto-padded."
            )
        if s.duration_seconds > PIPELINE_MAX_SHOT_DURATION_S:
            raise ValueError(
                f"Scene {s.scene_id} duration {s.duration_seconds}s exceeds MAX "
                f"{PIPELINE_MAX_SHOT_DURATION_S}s. Should have been auto-split."
            )


# ============================================================
# STAGE 5 — Word Timestamps
# ============================================================
class WordTimestamp(BaseModel):
    word: str
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)


class WordTimestamps(BaseModel):
    words: list[WordTimestamp] = Field(min_length=1)


# ============================================================
# STAGE 5 — Edit Decisions (Remotion input)
# ============================================================
class SubtitleWord(BaseModel):
    word: str
    start: float
    end: float
    is_keyword: bool


class AudioConfig(BaseModel):
    voiceover: str
    music: str = ""
    music_volume: float = Field(ge=0.0, le=1.0)


class EditScene(BaseModel):
    scene_id: int
    duration_seconds: float = Field(ge=PIPELINE_MIN_SHOT_DURATION_S, le=PIPELINE_MAX_SHOT_DURATION_S)
    image_path: str
    image_prompt: str = ""
    motion_type: str
    character_expression: str
    character_position: str
    background_color_hex: str
    subtitle_keyword: str = ""
    voiceover_text: str = ""
    subtitle_words: list[SubtitleWord] = Field(default_factory=list)


class EditDecisions(BaseModel):
    total_duration_seconds: float = Field(ge=1.0)
    audio: AudioConfig
    scenes: list[EditScene] = Field(min_length=1)

    @field_validator("scenes")
    @classmethod
    def check_consecutive_motion(cls, v: list[EditScene]) -> list[EditScene]:
        for i in range(1, len(v)):
            if v[i].motion_type == v[i - 1].motion_type:
                raise ValueError(
                    f"EditScenes {v[i-1].scene_id} and {v[i].scene_id} have the same motion_type."
                )
        return v
