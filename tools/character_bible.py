"""Locked character + style template for consistent stick-figure visuals.

Design:
- CHARACTER_IDENTITY and STYLE_SUFFIX are LOCKED — identical in every prompt,
  so head shape, line style and proportions never drift.
- EXPRESSION_MAP turns script expressions (scared, happy, ...) into concrete
  stick-figure facial cues (eyebrow/eye/mouth geometry) — facial expression
  changes per scene, the character does not.
- BACKGROUND_TEXT turns the scene's bg_color + scene_type into a flat
  single-color backdrop with minimal props, staying in the explainer style.
- No text is ever baked into the AI image — keywords are overlaid later in
  Remotion as crisp, editable text.

The LLM only ever outputs scene_action / scene_objects / expression /
background metadata — it never touches the locked template.
"""

FIXED_SEED = 445197

CHARACTER_IDENTITY = (
    "a simple minimalist stick figure character, large round head made of a "
    "single thick black outline circle, pure white fill inside head, no hair, "
    "thin black line neck, very thin single black line body with no torso "
    "volume, thin black line arms bending at elbow, thin black line legs "
    "bending at knee, no hands or feet detail (lines simply end), "
    "side-angled three-quarter view, centered composition, character shown "
    "from head to feet"
)

STYLE_SUFFIX = (
    "flat vector illustration, 2D explainer video style, clean bold black "
    "line art, crisp uniform line weight, simple flat background, simple flat "
    "design, no color on character body, high contrast black and white "
    "character design, no shading, no gradients, no glossy, no drop shadows, "
    "no textures, no ambient occlusion, crisp hard edges between color "
    "shapes, elegant minimal composition with generous negative space, "
    "premium educational animation still frame, sharp clean linework"
)

NEGATIVE_PROMPT = (
    "text, letters, words, typography, captions, title text, writing, "
    "color on character, photorealistic, 3d render, textured, gradient, "
    "gradient shading, glossy, glossy highlight, drop shadow, shadow under "
    "character, shadow under object, ambient occlusion, shading, detailed "
    "face, realistic proportions, thick body, muscles, clothing details, "
    "hair, blurry, extra limbs, extra characters, watermark, logo, "
    "decorative border frame, colored rectangle border"
)

# strength range for img2img: lower = closer to reference shape
IMG2IMG_STRENGTH_MIN = 0.55
IMG2IMG_STRENGTH_MAX = 0.65

# --- per-scene variables ------------------------------------------------

EXPRESSION_MAP = {
    "neutral": "facial expression: two small black dot eyes, thin level straight eyebrows, small straight black line mouth",
    "happy": "facial expression: two small black dot eyes, thin raised eyebrows, wide upward curve smile",
    "sad": "facial expression: two small black dot eyes, thin eyebrows tilted slightly inward, small downward curve line mouth",
    "angry": "facial expression: two small black dot eyes, thin downward angled eyebrows close together, small pressed straight line mouth",
    "scared": "facial expression: wide open round white eyes with tiny black pupils, eyebrows raised very high, slightly open small mouth",
    "shocked": "facial expression: very large round white eyes with tiny black pupils, small open round mouth, eyebrows raised very high",
    "thinking": "facial expression: two small black dot eyes, one eyebrow raised higher than the other, small wavy line mouth",
    "confused": "facial expression: one eyebrow higher than the other, two small black dot eyes, small wavy line mouth, head tilted slightly",
    "curious": "facial expression: one eyebrow raised, two small black dot eyes, small straight line mouth, head tilted slightly",
    "confident": "facial expression: two small black dot eyes, level thin eyebrows, small slight smile",
    "worried": "facial expression: wide open round white eyes with tiny black pupils, one eyebrow higher than the other, small wavy line mouth",
    "serious": "facial expression: two small black dot eyes, level thin eyebrows, small pressed straight line mouth",
}

COLOR_NAMES = {
    "#1A1A1A": "dark charcoal gray",
    "#2F2F2F": "dark gray",
    "#F5ECD7": "warm cream",
    "#F5F0E8": "light cream",
    "#D4E8F0": "pale blue",
    "#0F0F0F": "near black",
    "#FFFFFF": "white",
    "#000000": "black",
    "#2C1810": "deep warm brown",
    "#D4AF37": "warm gold",
    "#8B0000": "dark red",
}

SCENE_BACKGROUND_TEMPLATES = {
    "character_solo": "background: a flat {color} backdrop with a thin black ground line",
    "character_with_prop": "background: a flat {color} backdrop with a thin black ground line",
    "character_in_room": "background: a flat {color} wall with a thin black floor line and a small simple window frame",
    "character_explaining": "background: a flat {color} backdrop with a simple whiteboard easel holding a simple black line chart",
    "timeline_scene": "background: a flat {color} backdrop with a thin black horizontal timeline line and round milestone dots",
    "text_focus": "background: a flat {color} backdrop with one large simple black outlined icon",
    "two_characters": "background: a flat {color} backdrop with a thin black ground line",
}


def _color_name(bg_color: str) -> str:
    """Map the scene hex color to a plain-English flat color name."""
    key = str(bg_color or "").strip().upper()
    if key in COLOR_NAMES:
        return COLOR_NAMES[key]
    try:
        hexv = key.lstrip("#")
        if len(hexv) == 6:
            r, g, b = (int(hexv[i:i + 2], 16) for i in (0, 2, 4))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum > 200:
                return "very light pastel gray"
            if lum < 60:
                return "very dark gray"
            return "mid-tone gray"
    except ValueError:
        pass
    return "dark charcoal gray"


def _expression_text(expression: str) -> str:
    expr = str(expression or "").strip().lower()
    for key, text in EXPRESSION_MAP.items():
        if key in expr:
            return text
    return EXPRESSION_MAP["neutral"]


def _background_text(scene_type: str, bg_color: str) -> str:
    template = SCENE_BACKGROUND_TEMPLATES.get(
        scene_type, SCENE_BACKGROUND_TEMPLATES["character_solo"]
    )
    return template.format(color=_color_name(bg_color))


def build_scene_prompt(scene_action: str = "", scene_objects: str = "",
                       expression: str = "", scene_type: str = "",
                       bg_color: str = "", background: str = "") -> str:
    """Assemble the full prompt: locked identity + per-scene variables.

    Args:
        scene_action: pose/action only (from the scene planner)
        scene_objects: props, icons, secondary elements
        expression: script expression word (mapped to facial cues)
        scene_type: used to pick the flat backdrop layout
        bg_color: scene hex color used to color the flat backdrop
        background: optional explicit background text override
    """
    parts = [CHARACTER_IDENTITY]
    parts.append(_expression_text(expression))
    if scene_action:
        parts.append(str(scene_action).strip())
    if scene_objects:
        parts.append(str(scene_objects).strip())
    if background:
        parts.append(str(background).strip())
    else:
        parts.append(_background_text(scene_type, bg_color))
    parts.append(STYLE_SUFFIX)
    return ", ".join(p for p in parts if p)


REFERENCE_PROMPT = (
    CHARACTER_IDENTITY
    + ", facial expression: neutral, two small black dot eyes, thin level straight eyebrows, small straight black line mouth"
    + ", standing neutral pose, arms at sides, facing forward"
    + ", background: a plain white backdrop"
    + ", " + STYLE_SUFFIX
)
