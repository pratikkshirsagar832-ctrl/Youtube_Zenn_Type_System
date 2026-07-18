"""Full end-to-end pipeline smoke test.

Runs all stages with a SHORT test script (1 minute) so it finishes quickly.
No image generation — all visuals are SVG rendered by Remotion.
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
    (project_dir / "audio").mkdir(parents=True, exist_ok=True)

    # ============== STAGE 1 ==============
    banner("STAGE 1/4 — Research (DeepSeek R1)")
    from tools.deepseek_client import run_research
    brief = await run_research(
        topic="Why ancient humans feared the dark",
        niche="dark_psychology",
    )
    print(f"OK | topic: {brief['topic']}")
    print(f"    | hook_angles: {len(brief['hook_angles'])} | key_facts: {len(brief['key_facts'])}")
    (project_dir / "research_brief.json").write_text(json.dumps(brief, indent=2))

    # ============== STAGE 2 ==============
    banner("STAGE 2/4 — Script (DeepSeek V3, 1 min for speed)")
    from tools.deepseek_client import write_script
    script = await write_script(research_brief=brief, duration_minutes=1, niche="dark_psychology")
    full_text = " ".join(s["voiceover_text"] for s in script["sections"])
    wc = len(full_text.split())
    pauses = full_text.count("...") + full_text.count("—")
    print(f"OK | title: {script['title']}")
    print(f"    | sections: {len(script['sections'])} | words: {wc} | pauses: {pauses}")
    (project_dir / "script.json").write_text(json.dumps(script, indent=2))

    # ============== STAGE 3 ==============
    banner("STAGE 3/4 — Scene Plan (DeepSeek V3)")
    from tools.deepseek_client import plan_scenes
    scenes = await plan_scenes(script=script)
    print(f"OK | total_scenes: {scenes['total_scenes']}")
    scene_types = [s.get("scene_type", "?") for s in scenes["scenes"]]
    print(f"    | scene_types: {scene_types}")
    bg_colors = [s.get("background", {}).get("bg_color", "?") for s in scenes["scenes"]]
    print(f"    | bg_colors: {bg_colors}")
    expressions = [s.get("character_expression", "?") for s in scenes["scenes"]]
    print(f"    | expressions: {expressions}")
    (project_dir / "scene_plan.json").write_text(json.dumps(scenes, indent=2))

    # ============== TTS ==============
    banner("STAGE — Piper TTS (Local)")
    from tools.piper_tts import generate_voiceover
    tts_out = generate_voiceover(
        sections=script["sections"],
        output_path=str(project_dir / "audio" / "voiceover.wav"),
    )
    print(f"OK | audio_path: {tts_out['audio_path']}")
    print(f"    | duration: {tts_out['duration_seconds']:.2f}s")

    # ============== Whisper ==============
    banner("STAGE — Word Timestamps (Groq Whisper)")
    from tools.whisper_timestamps import extract_word_timestamps
    timestamps = extract_word_timestamps(str(project_dir / "audio" / "voiceover.wav"))
    print(f"OK | words extracted: {len(timestamps['words'])}")
    (project_dir / "word_timestamps.json").write_text(json.dumps(timestamps, indent=2))

    # ============== Scene Aligner ==============
    banner("STAGE — Scene Aligner + Edit Decisions")
    from tools.scene_aligner import build_aligned_scenes, build_edit_decisions
    aligned = build_aligned_scenes(
        scene_plan=scenes,
        word_timestamps=timestamps,
        total_audio_duration=tts_out["duration_seconds"],
    )
    edit = build_edit_decisions(
        aligned_scenes=aligned,
        voiceover_path=str(project_dir / "audio" / "voiceover.wav"),
        total_audio_duration=tts_out["duration_seconds"],
    )
    print(f"OK | total_scenes in edit: {len(edit['scenes'])}")
    print(f"    | total_duration_seconds: {edit['total_duration_seconds']:.2f}")
    for s in edit["scenes"][:3]:
        bg_info = s.get("background", {})
        print(f"    | scene {s['scene_id']:03d}: {s['duration_seconds']:.2f}s | type={s['scene_type']} | bg={bg_info.get('bg_color','?')} | expr={s['character_expression']} | {len(s['subtitle_words'])} words")
    (project_dir / "edit_decisions.json").write_text(json.dumps(edit, indent=2))

    banner("END-TO-END SUCCESS")
    print(f"\nProject dir: {project_dir}")
    print(f"Edit decisions: {project_dir / 'edit_decisions.json'}")
    print(f"Next step: render with Remotion (npx remotion render NexusVideo <out>)")


asyncio.run(go())
