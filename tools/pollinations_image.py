"""Pollinations image generation for scene visuals (stick-figure style).

One 1920x1080 image per aligned scene. All prompts are assembled from the
locked template in tools.character_bible — the LLM only ever contributes
scene_action / scene_objects, never the character or style description.

Character consistency pipeline:
1. A master reference image (character_ref.jpg) is generated once with
   REFERENCE_PROMPT and FIXED_SEED (plain text-to-image).
2. Every scene is generated via the OpenAI-compatible /v1/images/edits
   endpoint (multipart) using character_ref.jpg as the input image, with
   strength 0.55-0.65 (config) and NEGATIVE_PROMPT, seeded with FIXED_SEED.
3. If reference-guided generation fails, falls back to plain prompt-only
   generation with the same locked template + FIXED_SEED.

API: GET {POLLINATIONS_BASE_URL}/{prompt}?width=...&height=...&seed=...&model=...&nologo=true
for plain generation; POST https://gen.pollinations.ai/v1/images/edits (multipart,
b64_json response) for reference-guided generation.
Both use a Bearer token when POLLINATIONS_API_KEY is set.
"""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import time
import urllib.parse
from pathlib import Path
from typing import Callable

import requests

from config import (
    POLLINATIONS_BASE_URL,
    POLLINATIONS_API_KEY,
    POLLINATIONS_MODEL,
    POLLINATIONS_WIDTH,
    POLLINATIONS_HEIGHT,
    POLLINATIONS_IMG2IMG_STRENGTH,
    POLLINATIONS_QUALITY,
    REFERENCE_IMAGE_PATH,
    PIPELINE_IMAGE_RETRY_ATTEMPTS,
    PIPELINE_IMAGE_RETRY_WAIT_S,
    PIPELINE_PARALLEL_IMAGE_REQUESTS,
)
from tools.character_bible import (
    FIXED_SEED,
    NEGATIVE_PROMPT,
    REFERENCE_PROMPT,
    build_scene_prompt as build_bible_prompt,
)

POLLINATIONS_EDIT_ENDPOINT = "https://gen.pollinations.ai/v1/images/edits"

MAX_PROMPT_CHARS = 1500

SCENE_TYPE_ACTIONS = {
    "character_solo": "standing alone in the center of the scene",
    "character_with_prop": "holding a symbolic object in one hand",
    "character_in_room": "standing inside a minimal empty room",
    "character_explaining": "teaching, pointing one arm at a simple whiteboard chart",
    "timeline_scene": "walking along a simple horizontal timeline path with milestone dots",
    "text_focus": "standing beside a single large simple icon",
    "two_characters": "standing face to face with another simple stick figure",
}


def _is_image(data: bytes) -> bool:
    """Reject non-image responses (HTML error pages, JSON, etc)."""
    if data[:3] == b"\xff\xd8\xff":  # JPEG
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":  # WebP
        return True
    return False


def _to_16x9(data: bytes) -> bytes:
    """Force 1920x1080 16:9. Square outputs are upscaled and centered on a
    white canvas (seamless for white-background stick-figure art)."""
    try:
        from PIL import Image
        import io
    except ImportError:
        return data
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return data
    w, h = img.size
    target_w, target_h = POLLINATIONS_WIDTH, POLLINATIONS_HEIGHT
    if abs(w / h - target_w / target_h) < 0.02 and w == target_w and h == target_h:
        return data
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    scale = min(target_w / w, target_h / h)
    resized = img.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                         Image.LANCZOS)
    x = (target_w - resized.width) // 2
    y = (target_h - resized.height) // 2
    canvas.paste(resized, (x, y))
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def build_scene_prompt(scene: dict, scene_num: int) -> str:
    """Assemble the full prompt from the locked bible + scene metadata.

    scene_action is derived from the scene type; the character expression
    and background color/layout come straight from the script's scene
    planner, so each scene looks different while the character stays locked.
    """
    scene_type = scene.get("scene_type", "character_solo")
    action = scene.get("scene_action", "") or SCENE_TYPE_ACTIONS.get(
        scene_type, SCENE_TYPE_ACTIONS["character_solo"]
    )

    expression = scene.get("character_expression", "") or ""
    bg = scene.get("background", {})
    bg_color = bg.get("bg_color", "#FFFFFF") if isinstance(bg, dict) else "#FFFFFF"

    objects: list[str] = []
    props = scene.get("props", [])
    if props:
        objects.append(", ".join(str(p) for p in props))
    voiceover = scene.get("voiceover_text", "") or scene.get("transcribed_text", "")
    snippet = " ".join(str(voiceover).split())[:120]
    if snippet:
        objects.append(f"scene context: {snippet}")

    prompt = build_bible_prompt(
        scene_action=action,
        scene_objects=", ".join(objects),
        expression=expression,
        scene_type=scene_type,
        bg_color=bg_color,
    )
    return prompt[:MAX_PROMPT_CHARS]


def _fetch_image(prompt: str, output_path: str, seed: int,
                 retries: int | None = None, wait_s: float | None = None) -> None:
    """Download one plain image with retries + backoff. Raises on failure."""
    retries = retries if retries is not None else PIPELINE_IMAGE_RETRY_ATTEMPTS
    wait_s = wait_s if wait_s is not None else PIPELINE_IMAGE_RETRY_WAIT_S
    base = POLLINATIONS_BASE_URL.rstrip("/")
    headers = {}
    if POLLINATIONS_API_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

    query = urllib.parse.urlencode({
        "width": POLLINATIONS_WIDTH,
        "height": POLLINATIONS_HEIGHT,
        "seed": seed,
        "model": POLLINATIONS_MODEL,
        "quality": POLLINATIONS_QUALITY,
        "nologo": "true",
    })
    url = f"{base}/{urllib.parse.quote(prompt)}?{query}"

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=300)
            if resp.status_code == 200 and _is_image(resp.content):
                Path(output_path).write_bytes(resp.content)
                return
            last_err = RuntimeError(
                f"Pollinations returned HTTP {resp.status_code}, "
                f"content-type={resp.headers.get('content-type', '?')}"
            )
            print(f"[pollinations] attempt {attempt}: {last_err}", flush=True)
        except Exception as e:  # noqa: BLE001 - retry on any transport failure
            last_err = e
            print(f"[pollinations] attempt {attempt}: {type(e).__name__}: {e}", flush=True)

        if attempt < retries:
            time.sleep(wait_s)

    raise RuntimeError(f"Pollinations image failed after {retries} attempts: {last_err}")


def _fetch_image_with_reference(prompt: str, reference_image: str, output_path: str,
                                seed: int, strength: float | None = None,
                                retries: int | None = None,
                                wait_s: float | None = None) -> None:
    """Generate an image guided by a reference image (character anchor).

    POSTs to the OpenAI-compatible /v1/images/edits endpoint with the
    reference file as multipart; response is JSON with b64_json. The
    negative prompt and strength keep the character locked to the reference.
    """
    retries = retries if retries is not None else PIPELINE_IMAGE_RETRY_ATTEMPTS
    wait_s = wait_s if wait_s is not None else PIPELINE_IMAGE_RETRY_WAIT_S
    headers = {}
    if POLLINATIONS_API_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

    ref_path = Path(reference_image)
    mime = "image/png" if ref_path.suffix.lower() == ".png" else "image/jpeg"

    payload = {
        "prompt": prompt,
        "model": POLLINATIONS_MODEL,
        "width": POLLINATIONS_WIDTH,
        "height": POLLINATIONS_HEIGHT,
        "seed": seed,
        "nologo": "true",
        "quality": POLLINATIONS_QUALITY,
        "strength": strength if strength is not None else POLLINATIONS_IMG2IMG_STRENGTH,
        "negative_prompt": NEGATIVE_PROMPT,
    }

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with open(reference_image, "rb") as fh:
                resp = requests.post(
                    POLLINATIONS_EDIT_ENDPOINT,
                    files={"image": (ref_path.name, fh, mime)},
                    data=payload,
                    headers=headers,
                    timeout=300,
                )
            if resp.status_code == 200:
                data = resp.json()
                b64 = data.get("data", [{}])[0].get("b64_json")
                if b64:
                    image = base64.b64decode(b64)
                    if _is_image(image):
                        Path(output_path).write_bytes(_to_16x9(image))
                        return
            last_err = RuntimeError(
                f"Pollinations edits returned HTTP {resp.status_code}, "
                f"content-type={resp.headers.get('content-type', '?')}"
            )
            print(f"[pollinations] edits attempt {attempt}: {last_err}", flush=True)
        except Exception as e:  # noqa: BLE001 - retry on any transport failure
            last_err = e
            print(f"[pollinations] edits attempt {attempt}: {type(e).__name__}: {e}", flush=True)

        if attempt < retries:
            time.sleep(wait_s)

    raise RuntimeError(
        f"Pollinations reference image failed after {retries} attempts: {last_err}"
    )


async def generate_scene_images(
    scenes: list[dict],
    output_dir: str,
    slug: str,
    on_progress: Callable[[int, int], None] | None = None,
    concurrency: int | None = None,
    use_reference: bool = True,
) -> list[str]:
    """Generate one 16:9 image per scene (parallel, limited concurrency).

    Args:
        scenes: aligned scenes (each with voiceover_text, scene_type, etc.)
        output_dir: local dir where scene_XXX.jpg files are written
        slug: project slug used for the Remotion-relative image path
        on_progress: callback(i+1, n) per completed image
        concurrency: max parallel requests
        use_reference: generate a character_ref.jpg anchor (FIXED_SEED) and
            guide every scene with it (character consistency). Falls back to
            prompt-only generation on failure.

    Returns:
        list of Remotion-relative paths, e.g. ["<slug>/images/scene_001.jpg", ...]
    """
    concurrency = concurrency or PIPELINE_PARALLEL_IMAGE_REQUESTS
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)

    ref_path: Path | None = None
    if scenes and use_reference:
        ref_path = out_dir / "character_ref.png"
        source = Path(REFERENCE_IMAGE_PATH)
        if source.exists():
            try:
                shutil.copy(source, ref_path)
                print(f"[pollinations] using user reference image: {source}", flush=True)
            except Exception as e:  # noqa: BLE001
                ref_path = None
                print(f"[pollinations] reference copy failed: {e}", flush=True)
        else:
            try:
                await asyncio.to_thread(
                    _fetch_image, REFERENCE_PROMPT, str(ref_path), seed=FIXED_SEED
                )
                print(f"[pollinations] generated character reference: {ref_path}", flush=True)
            except Exception as e:  # noqa: BLE001 - anchor optional
                ref_path = None
                print(f"[pollinations] reference anchor failed, using prompt only: {e}", flush=True)

    async def one(i: int, scene: dict) -> str:
        async with sem:
            local = out_dir / f"scene_{i + 1:03d}.jpg"
            prompt = build_scene_prompt(scene, i + 1)
            if ref_path is not None:
                try:
                    await asyncio.to_thread(
                        _fetch_image_with_reference, prompt, str(ref_path), str(local),
                        seed=FIXED_SEED,
                    )
                    return f"{slug}/images/{local.name}"
                except Exception as e:  # noqa: BLE001 - per-scene fallback
                    print(f"[pollinations] scene {i + 1} edits failed: {e}", flush=True)
            await asyncio.to_thread(_fetch_image, prompt, str(local), seed=FIXED_SEED)
            return f"{slug}/images/{local.name}"

    results = await asyncio.gather(*[one(i, s) for i, s in enumerate(scenes)])
    if on_progress:
        for i in range(len(results)):
            on_progress(i + 1, len(results))
    return results


if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else REFERENCE_PROMPT
    out = sys.argv[2] if len(sys.argv) > 2 else "./test_image.jpg"
    print(f"Generating: {prompt[:80]}...")
    _fetch_image(prompt, out, seed=FIXED_SEED)
    print(json.dumps({"output": out, "bytes": Path(out).stat().st_size}))
