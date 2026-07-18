"""Constants for scene types, expressions, backgrounds, props, and motions.

Used by config.py, pydantic_models.py, deepseek prompts, and pipeline.
"""

SCENE_TYPES = [
    "character_solo",
    "character_with_prop",
    "character_in_room",
    "character_explaining",
    "timeline_scene",
    "text_focus",
    "two_characters",
]

CHARACTER_EXPRESSIONS = [
    "neutral",
    "curious",
    "shocked",
    "thinking",
    "sad",
    "confident",
    "scared",
    "confused",
]

CHARACTER_POSITIONS = ["left", "center", "right"]

CHARACTER_ANIMATIONS = [
    "idle",
    "walk_in_left",
    "walk_in_right",
    "walk_out_left",
    "point_up",
]

BACKGROUND_TYPES = [
    "plain_white",
    "plain_cream",
    "plain_blue",
    "room_simple",
    "timeline",
    "chalkboard",
    "outdoor_simple",
    "split_screen",
]

AVAILABLE_PROPS = [
    "SkullProp",
    "FireProp",
    "BrainProp",
    "ClockProp",
    "HeartProp",
    "QuestionMarkProp",
    "BookProp",
    "MirrorProp",
    "ChainProp",
]

PROP_POSITIONS = ["left_of_character", "right_of_character", "above"]

MOTION_TYPES = [
    "zoom_in_slow",
    "zoom_out_slow",
    "pan_left",
    "pan_right",
    "static",
]
