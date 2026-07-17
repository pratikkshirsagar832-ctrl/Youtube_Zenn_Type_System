"""Pexels fallback for image generation.

Used when Pollinations fails for a specific scene. Searches Pexels for a relevant
stock photo and downloads it.
"""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

import httpx

from config import PEXELS_API_KEY


def fetch_pexels_image(search_query: str, scene_id: int, output_dir: str) -> dict:
    """Search Pexels for an image, download first result. Returns status dict."""
    if not PEXELS_API_KEY or PEXELS_API_KEY.startswith("your_"):
        return {
            "scene_id": scene_id,
            "status": "failed",
            "error": "PEXELS_API_KEY not set",
        }

    output_path = Path(output_dir) / f"scene_{scene_id:03d}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": search_query[:100], "per_page": 1, "orientation": "landscape"}
        with httpx.Client(timeout=30.0) as client:
            r = client.get("https://api.pexels.com/v1/search", headers=headers, params=params)
            if r.status_code != 200:
                return {"scene_id": scene_id, "status": "failed", "error": f"search HTTP {r.status_code}"}
            data = r.json()
            photos = data.get("photos", [])
            if not photos:
                return {"scene_id": scene_id, "status": "failed", "error": "no photos found"}
            photo = photos[0]
            # Get largest available size
            src = photo.get("src", {})
            image_url = src.get("landscape") or src.get("large") or src.get("original")
            if not image_url:
                return {"scene_id": scene_id, "status": "failed", "error": "no image src"}

            img_resp = client.get(image_url, timeout=60.0)
            if img_resp.status_code != 200 or len(img_resp.content) < 5000:
                return {"scene_id": scene_id, "status": "failed", "error": "download failed"}

            output_path.write_bytes(img_resp.content)
            return {
                "scene_id": scene_id,
                "image_path": str(output_path),
                "source": "pexels",
                "status": "ok",
            }
    except Exception as e:
        return {"scene_id": scene_id, "status": "failed", "error": f"{type(e).__name__}: {e}"}
