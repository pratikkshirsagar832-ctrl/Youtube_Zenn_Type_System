"""Full end-to-end pipeline smoke test.

Runs all 5 stages with a SHORT test script (1 minute = 60s, 5 sections) so it
finishes in <5 minutes. Skips Remotion render (slow, separate concern).
"""
import sys
import json
import time
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def banner(s):
    print("\n" + "=" * 70)
    print(s)
    print("=" * 70)


async def go():
    project_id = f"smoke_{int(time.time())}"
    project_dir = ROOT / "projects" / project_id
    (project_dir / "images").mkdir(parents=True, exist_ok=True)
    (project_dir / "audio").mkdir(parents=True, exist_ok=True)

    # ============== STAGE 1 ==============
    banner("STAGE 1/5 — Research (DeepSeek R1)")
    from tools.deepseek_client import run_research
    brief = await run_research(
        topic="Why ancient humans feared the dark",
        niche="dark_psychology",
    )
    print(f"OK | topic: {brief['topic']}")
    print(f"    | hook_angles: {len(brief['hook_angles'])} | key_facts: {len(brief['key_facts'])}")
    (project_dir / "research_brief.json").write_text(json.dumps(brief, indent=2))

    # ============== STAGE 2 ==============
    banner("STAGE 2/5 — Script (DeepSeek V3, 1 min for speed)")
    from tools.deepseek_client import write_script
    script = await write_script(research_brief=brief, duration_minutes=1, niche="dark_psychology")
    full_text = " ".join(s["voiceover_text"] for s in script["sections"])
    wc = len(full_text.split())
    pauses = full_text.count("...") + full_text.count("—")
    print(f"OK | title: {script['title']}")
    print(f"    | sections: {len(script['sections'])} | words: {wc} | pauses: {pauses}")
    (project_dir / "script.json").write_text(json.dumps(script, indent=2))

    # ============== STAGE 3 ==============
    banner("STAGE 3/5 — Scene Plan (DeepSeek V3)")
    from tools.deepseek_client import plan_scenes
    scenes = await plan_scenes(script=script)
    print(f"OK | total_scenes: {scenes['total_scenes']}")
    motion_types = [s["motion_type"] for s in scenes["scenes"]]
    bad = sum(1 for i in range(len(motion_types) - 1) if motion_types[i] == motion_types[i + 1])
    print(f"    | motion_types: {motion_types}")
    print(f"    | consecutive-same-motion violations: {bad}")
    bg_colors = [s["background_color_hex"] for s in scenes["scenes"]]
    print(f"    | bg colors: {bg_colors}")
    (project_dir / "scene_plan.json").write_text(json.dumps(scenes, indent=2))

    # ============== STAGE 4 — TTS ==============
    banner("STAGE 4a/5 — Piper TTS (Local)")
    from tools.piper_tts import generate_voiceover
    tts_out = generate_voiceover(
        sections=script["sections"],
        output_path=str(project_dir / "audio" / "voiceover.wav"),
    )
    print(f"OK | audio_path: {tts_out['audio_path']}")
    print(f"    | duration: {tts_out['duration_seconds']:.2f}s")

    # ============== STAGE 4 — Images ==============
    banner("STAGE 4b/5 — Pollinations Image Generation")
    from tools.pollinations_image import generate_images_batch
    img_results = await generate_images_batch(
        scenes=scenes["scenes"],
        output_dir=str(project_dir / "images"),
    )
    ok = sum(1 for r in img_results if r.get("status") == "ok")
    print(f"OK | images generated: {ok}/{len(img_results)}")
    for r in img_results:
        if r.get("status") == "ok":
            print(f"    | scene {r['scene_id']:03d}: {r['image_path']} ({Path(r['image_path']).stat().st_size} bytes)")

    # ============== STAGE 5 — Whisper (Groq) ==============
    banner("STAGE 5a/5 — Word Timestamps (Groq Whisper)")
    from tools.whisper_timestamps import extract_word_timestamps
    timestamps = extract_word_timestamps(str(project_dir / "audio" / "voiceover.wav"))
    print(f"OK | words extracted: {len(timestamps['words'])}")
    (project_dir / "word_timestamps.json").write_text(json.dumps(timestamps, indent=2))

    # ============== STAGE 5 — Scene Aligner ==============
    banner("STAGE 5b/5 — Scene Aligner")
    from tools.scene_aligner import build_edit_decisions
    edit = build_edit_decisions(
        scene_plan=scenes,
        word_timestamps=timestamps,
        voiceover_path=str(project_dir / "audio" / "voiceover.wav"),
    )
    print(f"OK | total_scenes in edit: {len(edit['scenes'])}")
    print(f"    | total_duration_seconds: {edit['total_duration_seconds']:.2f}")
    for s in edit["scenes"][:3]:
        print(f"    | scene {s['scene_id']:03d}: {s['duration_seconds']:.2f}s | motion={s['motion_type']} | expr={s['character_expression']} | {len(s['subtitle_words'])} words")
    (project_dir / "edit_decisions.json").write_text(json.dumps(edit, indent=2))

    banner("END-TO-END SUCCESS")
    print(f"\nProject dir: {project_dir}")
    print(f"Edit decisions: {project_dir / 'edit_decisions.json'}")
    print(f"Next step: render with Remotion (npx remotion render NexusVideo <out>)")


asyncio.run(go())
