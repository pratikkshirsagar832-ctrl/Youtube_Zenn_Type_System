import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { SceneRenderer, SceneData } from "./components/SceneRenderer";
import { SubtitleWord } from "./SubtitleLayer";

export interface NexusScene {
  scene_id: number;
  duration_seconds: number;
  image_path: string;
  motion_type: string;
  subtitle_keyword: string;
  subtitle_words: SubtitleWord[];
  [key: string]: unknown;
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
  [key: string]: unknown;
}

const NexusSceneBlock: React.FC<{
  scene: NexusScene;
  startFrame: number;
  durationInFrames: number;
}> = ({ scene, startFrame, durationInFrames }) => {
  return (
    <Sequence from={startFrame} durationInFrames={durationInFrames}>
      <SceneRenderer scene={scene as unknown as SceneData} />
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
