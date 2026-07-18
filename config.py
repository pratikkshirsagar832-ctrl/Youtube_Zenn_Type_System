"""Nexus config — loads .env and exposes typed settings."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def _get(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


def _get_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _get_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


# --- Supabase ---
SUPABASE_URL = _get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = _get("SUPABASE_ANON_KEY", "")

# --- DeepSeek ---
DEEPSEEK_API_KEY = _get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = _get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL_REASONING = _get("DEEPSEEK_MODEL_REASONING", "deepseek-reasoner")
DEEPSEEK_MODEL_CHAT = _get("DEEPSEEK_MODEL_CHAT", "deepseek-chat")

# --- Channel ---
CHANNEL_NAME = _get("CHANNEL_NAME", "Nexus Mind")
TARGET_AUDIENCE = _get("TARGET_AUDIENCE", "Dark Psychology & Human Behavior enthusiasts, USA")
DEFAULT_DURATION_MINUTES = _get_int("DEFAULT_DURATION_MINUTES", 8)
DEFAULT_NICHE = _get("DEFAULT_NICHE", "dark_psychology")

# --- Piper TTS ---
PIPER_MODEL_PATH = str(PROJECT_ROOT / _get("PIPER_MODEL_PATH", "./models/en_US-ryan-high.onnx").lstrip("./"))
PIPER_CONFIG_PATH = str(PROJECT_ROOT / _get("PIPER_CONFIG_PATH", "./models/en_US-ryan-high.onnx.json").lstrip("./"))
PIPER_VOICE_NAME = _get("PIPER_VOICE_NAME", "en_US-ryan-high")

# --- Groq (Whisper API for word timestamps) ---
GROQ_API_KEY = _get("GROQ_API_KEY", "")
GROQ_BASE_URL = _get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
WHISPER_MODEL = _get("WHISPER_MODEL", "whisper-large-v3")
WHISPER_LANGUAGE = _get("WHISPER_LANGUAGE", "en")

# --- Remotion ---
REMOTION_PROJECT_PATH = str(PROJECT_ROOT / _get("REMOTION_PROJECT_PATH", "./remotion-composer").lstrip("./"))
REMOTION_COMPOSITION = _get("REMOTION_COMPOSITION", "NexusVideo")
REMOTION_OUTPUT_DIR = str(PROJECT_ROOT / _get("REMOTION_OUTPUT_DIR", "./projects").lstrip("./"))
CHROME_EXECUTABLE = _get("CHROME_EXECUTABLE", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe")

# --- Pipeline ---
PIPELINE_MIN_SHOT_DURATION_S = _get_float("PIPELINE_MIN_SHOT_DURATION_S", 1.0)
PIPELINE_MAX_SHOT_DURATION_S = _get_float("PIPELINE_MAX_SHOT_DURATION_S", 10.0)
PIPELINE_DEFAULT_FPS = _get_int("PIPELINE_DEFAULT_FPS", 30)

# --- Server ---
BACKEND_HOST = _get("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = _get_int("BACKEND_PORT", 8000)
FRONTEND_URL = _get("FRONTEND_URL", "http://localhost:3000")

# --- Project paths ---
PROJECTS_DIR = PROJECT_ROOT / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)

# --- Scene pacing constants (imported from lib.pacing) ---
from lib.pacing import (
    SCENE_TYPES,
    CHARACTER_EXPRESSIONS,
    CHARACTER_POSITIONS,
    CHARACTER_ANIMATIONS,
    BACKGROUND_TYPES,
    AVAILABLE_PROPS,
    PROP_POSITIONS,
    MOTION_TYPES,
)

# --- Niches ---
VALID_NICHES = ["dark_psychology", "human_behavior"]
NICHE_LABELS = {
    "dark_psychology": "Dark Psychology",
    "human_behavior": "Human Behavior",
}


def is_fully_configured() -> dict:
    """Check which external services are configured. Returns dict of name -> bool."""
    return {
        "deepseek": bool(DEEPSEEK_API_KEY) and not DEEPSEEK_API_KEY.startswith("your_"),
        "supabase": bool(SUPABASE_URL) and not SUPABASE_URL.startswith("your_"),
        "piper_model_exists": Path(PIPER_MODEL_PATH).exists(),
        "remotion_node_modules": Path(REMOTION_PROJECT_PATH, "node_modules").exists(),
    }
