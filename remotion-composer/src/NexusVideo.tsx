import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { DynamicImage, MotionType } from "./DynamicImage";
import { SubtitleLayer, SubtitleWord } from "./SubtitleLayer";

// ---------------------------------------------------------------------------
// NexusVideo — main composition for the Nexus pipeline.
// 2 layers per scene:
//   1. DynamicImage (Ken Burns background)
//   2. SubtitleLayer (word-by-word gold captions)
// + audio (voiceover at full volume, music at 25% if present).
// ---------------------------------------------------------------------------

export interface NexusScene {
  scene_id: number;
  duration_seconds: number;
  image_path: string;
  image_prompt?: string;
  motion_type: MotionType;
  background_color_hex: string;
  subtitle_keyword?: string;
  voiceover_text?: string;
  subtitle_words: SubtitleWord[];
}

export interface NexusAudio {
  voiceover: string;
  music: string;
  music_volume: number;
}

export interface NexusVideoProps {
  total_duration_seconds: number;
  audio: NexusAudio;
  scenes: NexusScene[];
}

const NexusSceneBlock: React.FC<{
  scene: NexusScene;
  startFrame: number;
  durationInFrames: number;
}> = ({ scene, startFrame, durationInFrames }) => {
  return (
    <Sequence from={startFrame} durationInFrames={durationInFrames}>
      <AbsoluteFill>
        <DynamicImage
          imagePath={scene.image_path}
          motionType={scene.motion_type}
          durationInFrames={durationInFrames}
          backgroundColor={scene.background_color_hex}
        />
        <SubtitleLayer words={scene.subtitle_words} />
      </AbsoluteFill>
    </Sequence>
  );
};

export const NexusVideo: React.FC<NexusVideoProps> = ({
  audio,
  scenes,
}) => {
  const { fps } = useVideoConfig();
  let cursor = 0;
  const blocks = scenes.map((scene) => {
    const startFrame = cursor;
    const durationInFrames = Math.max(1, Math.round(scene.duration_seconds * fps));
    cursor += durationInFrames;
    return { scene, startFrame, durationInFrames };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0F" }}>
      {blocks.map((b) => (
        <NexusSceneBlock
          key={b.scene.scene_id}
          scene={b.scene}
          startFrame={b.startFrame}
          durationInFrames={b.durationInFrames}
        />
      ))}

      {audio.voiceover && (
        <Audio
          src={staticFile(audio.voiceover)}
          volume={1}
        />
      )}

      {audio.music && (
        <Audio
          src={staticFile(audio.music)}
          volume={audio.music_volume ?? 0.25}
        />
      )}
    </AbsoluteFill>
  );
};
