"""Remotion render driver.

Spawns `npx remotion render` to generate the final MP4.
Copies only audio into remotion-composer/public/{slug}/ before rendering.
No images — all visuals are SVG rendered by Remotion.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from config import (
    CHROME_EXECUTABLE,
    REMOTION_PROJECT_PATH,
    REMOTION_COMPOSITION,
    PROJECTS_DIR,
)


def _safe_slug(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:50]


def render_video(project_id: str, edit_decisions: dict, output_path: str) -> dict:
    """Copy audio into remotion-composer/public/{slug}/ and spawn npx render."""
    project_dir = PROJECTS_DIR / project_id
    topic_slug = _safe_slug(project_id)

    target_dir = Path(REMOTION_PROJECT_PATH) / "public" / topic_slug
    target_audio = target_dir / "audio"
    target_audio.mkdir(parents=True, exist_ok=True)

    # Copy audio
    src_audio = project_dir / "audio"
    if src_audio.exists():
        for f in src_audio.glob("*.wav"):
            shutil.copy(f, target_audio / f.name)

    # Rewrite edit_decisions.json to use public/{slug}/ paths for audio
    props = dict(edit_decisions)
    voiceover = props.get("audio", {}).get("voiceover", "")
    if voiceover:
        if voiceover.startswith("audio/"):
            props["audio"]["voiceover"] = f"{topic_slug}/{voiceover}"
        else:
            props["audio"]["voiceover"] = f"{topic_slug}/audio/{Path(voiceover).name}"

    props_path = target_dir / "props.json"
    props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")

    # Spawn npx remotion render
    props_arg = str(props_path).replace("\\", "/")
    browser_flag = ""
    if CHROME_EXECUTABLE:
        browser_flag = f' --browser-executable="{CHROME_EXECUTABLE}"'

    cmd_str = (
        f'npx remotion render "{REMOTION_COMPOSITION}" '
        f'"{output_path}" --props="{props_arg}"{browser_flag} --no-cache'
    )
    print(f"[remotion] Running: {cmd_str}", flush=True)

    env = {
        **os.environ,
        "REMOTION_WEBPACK_CACHE_ENABLED": "0",
    }

    proc = subprocess.run(
        cmd_str,
        cwd=REMOTION_PROJECT_PATH,
        check=False,
        text=True,
        shell=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Remotion render failed (code {proc.returncode})")

    if not Path(output_path).exists():
        raise RuntimeError(f"Remotion finished but MP4 not found at {output_path}")

    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"[remotion] MP4 written: {output_path} ({size_mb:.1f} MB)", flush=True)
    return {
        "output_path": str(output_path),
        "file_size_mb": size_mb,
        "total_duration_seconds": props.get("total_duration_seconds", 0.0),
    }
