"""Pollinations Flux image generation.

Primary:  gen.pollinations.ai/image/{prompt}  (authenticated, model=flux)
Fallback: Pexels stock photo

API key:  POLLINATIONS_API_KEY in .env (sk_...)
Cost:     ~0.00175 pollen per 1024x1024 Flux Schnell image (~$0.00175)
"""
import os
import time
import asyncio
from pathlib import Path
from urllib.parse import quote

import httpx

from config import POLLINATIONS_BASE_URL


DEFAULT_MODEL = "flux"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MAX_RETRIES = 3
RETRY_BACKOFF_S = 2.0
DOWNLOAD_TIMEOUT_S = 120.0


def _get_api_key() -> str:
    """Return the Pollinations API key (sk_ or pk_), or empty string."""
    return os.getenv("POLLINATIONS_API_KEY", "").strip()


def _build_headers() -> dict:
    """Build auth headers. Bearer is preferred; key is also passed as ?key=."""
    key = _get_api_key()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _build_url(prompt: str, seed: int, width: int = DEFAULT_WIDTH,
               height: int = DEFAULT_HEIGHT, model: str = DEFAULT_MODEL) -> str:
    """Build the authenticated Pollinations image URL.

    Uses a fixed seed so the stickman character is consistent across all images.
    Forces white background and black stickman for visual consistency.
    """
    base = "https://gen.pollinations.ai/image"
    encoded = quote(prompt, safe="")
    url = f"{base}/{encoded}?model={model}&width={width}&height={height}&seed={seed}&nologo=true&enhance=false"
    key = _get_api_key()
    if key:
        url = f"{url}&key={key}"
    return url


def _save_image(content: bytes, scene_id: int | str, output_dir: str) -> str:
    """Write image bytes to {output_dir}/scene_{scene_id:03d}.jpg and return the path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"scene_{int(scene_id):03d}.jpg"
    out_path.write_bytes(content)
    return str(out_path)


def _pexels_fallback(prompt: str, scene_id: int | str, output_dir: str,
                     reason: str) -> dict:
    """Try Pexels stock photo as a last resort when Pollinations fails."""
    try:
        from tools.pexels_fallback import fetch_photo
        path, status, err = fetch_photo(prompt, scene_id, output_dir)
        if status == "ok":
            return {
                "scene_id": int(scene_id),
                "image_path": path,
                "source": "pexels",
                "status": "ok",
                "fallback_reason": reason,
            }
        return {
            "scene_id": int(scene_id),
            "image_path": None,
            "source": "none",
            "status": "failed",
            "error": f"pollinations={reason}; pexels={err}",
        }
    except Exception as e:
        return {
            "scene_id": int(scene_id),
            "image_path": None,
            "source": "none",
            "status": "failed",
            "error": f"pollinations={reason}; pexels_exception={e}",
        }


def generate_image(prompt: str, scene_id: int | str, output_dir: str, seed: int = 42) -> dict:
    """Generate a single image via Pollinations turbo with retry + Pexels fallback.

    Uses a fixed seed so the character is consistent across all images.

    Returns a dict with keys: scene_id, image_path, source, status, [error, fallback_reason].
    """
    key = _get_api_key()
    if not key:
        return {
            "scene_id": int(scene_id),
            "image_path": None,
            "source": "none",
            "status": "failed",
            "error": "POLLINATIONS_API_KEY missing in .env",
        }

    url = _build_url(prompt, seed=seed)
    headers = _build_headers()

    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=DOWNLOAD_TIMEOUT_S, follow_redirects=True) as client:
                r = client.get(url, headers=headers)
            if r.status_code == 200 and len(r.content) > 1000:
                path = _save_image(r.content, scene_id, output_dir)
                return {
                    "scene_id": int(scene_id),
                    "image_path": path,
                    "source": "pollinations",
                    "status": "ok",
                }
            if r.status_code == 402:
                last_err = f"402_insufficient_pollen_balance (balance check enter.pollinations.ai)"
            elif r.status_code == 401:
                last_err = f"401_unauthorized (check POLLINATIONS_API_KEY)"
            elif r.status_code == 429:
                last_err = f"429_rate_limited"
            else:
                body_snip = r.text[:160].replace("\n", " ")
                last_err = f"http_{r.status_code}: {body_snip}"
        except httpx.TimeoutException:
            last_err = f"timeout after {DOWNLOAD_TIMEOUT_S}s"
        except Exception as e:
            last_err = f"exception: {type(e).__name__}: {e}"

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_S * attempt)

    return _pexels_fallback(prompt, scene_id, output_dir, reason=last_err)


async def generate_image_async(prompt: str, scene_id: int | str, output_dir: str, seed: int = 42) -> dict:
    """Async wrapper around generate_image using to_thread so the event loop
    stays responsive while we wait on a network-bound image call."""
    return await asyncio.to_thread(generate_image, prompt, scene_id, output_dir, seed)


async def generate_images_batch(scenes: list[dict], output_dir: str,
                                max_concurrent: int = 3,
                                project_seed: int = 42) -> list[dict]:
    """Generate images for all scenes in parallel, with a small concurrency cap.

    All images use the same project_seed so the stickman character is consistent
    across all scenes. Only the prompt changes to reflect scene-specific content.

    Each scene must contain at least 'scene_id' and either 'image_prompt' or
    'prompt'.
    """
    sem = asyncio.Semaphore(max_concurrent)

    async def _one(scene: dict) -> dict:
        scene_id = scene.get("scene_id")
        prompt = scene.get("image_prompt") or scene.get("prompt") or scene.get("description", "")
        async with sem:
            return await generate_image_async(prompt, scene_id, output_dir, seed=project_seed)

    tasks = [_one(s) for s in scenes]
    return await asyncio.gather(*tasks)
