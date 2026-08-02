import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SubtitleLayer, SubtitleWord } from "../SubtitleLayer";

export interface SceneData {
  scene_id: number;
  duration_seconds: number;
  image_path: string;
  motion_type: string;
  subtitle_keyword: string;
  subtitle_words: SubtitleWord[];
  [key: string]: unknown;
}

interface SceneRendererProps {
  scene: SceneData;
}

type MotionVariant = "zoom_in_slow" | "zoom_out_slow" | "pan_left" | "pan_right" | "static";

// Pan needs overscan so the image never reveals edges.
const PAN_SCALE = 1.12;
const PAN_PX = 70;

const MOTIONS: Record<string, { from: { scale: number; x: number }; to: { scale: number; x: number } }> = {
  zoom_in_slow: { from: { scale: 1.0, x: 0 }, to: { scale: 1.12, x: 0 } },
  zoom_out_slow: { from: { scale: 1.12, x: 0 }, to: { scale: 1.0, x: 0 } },
  pan_left: { from: { scale: PAN_SCALE, x: 0 }, to: { scale: PAN_SCALE, x: -PAN_PX } },
  pan_right: { from: { scale: PAN_SCALE, x: PAN_PX }, to: { scale: PAN_SCALE, x: 0 } },
  static: { from: { scale: 1.0, x: 0 }, to: { scale: 1.0, x: 0 } },
};

export const SceneRenderer: React.FC<SceneRendererProps> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = Math.max(1, Math.round(scene.duration_seconds * fps));

  const motion = MOTIONS[scene.motion_type as MotionVariant] ?? MOTIONS.static;
  const p = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = motion.from.scale + (motion.to.scale - motion.from.scale) * p;
  const x = motion.from.x + (motion.to.x - motion.from.x) * p;
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0A0A0F" }}>
      {scene.image_path ? (
        <Img
          src={staticFile(scene.image_path)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `translateX(${x}px) scale(${scale})`,
            opacity,
          }}
        />
      ) : null}

      {/* Scene keyword — crisp title word overlay (never baked into the AI image) */}
      {scene.subtitle_keyword ? (
        <div
          style={{
            position: "absolute",
            top: 48,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            pointerEvents: "none",
          }}
        >
          <span
            style={{
              fontFamily: "Arial, Helvetica, sans-serif",
              fontWeight: 900,
              fontSize: 76,
              letterSpacing: 6,
              textTransform: "uppercase",
              color: "#FFFFFF",
              textShadow: "0 3px 18px rgba(0,0,0,0.85), 0 0 8px rgba(0,0,0,0.6)",
            }}
          >
            {scene.subtitle_keyword}
          </span>
        </div>
      ) : null}

      {/* Cinematic vignette + bottom gradient for caption readability */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.45) 100%), " +
            "linear-gradient(transparent 55%, rgba(0,0,0,0.55) 100%)",
          pointerEvents: "none",
        }}
      />

      <SubtitleLayer words={scene.subtitle_words} />
    </AbsoluteFill>
  );
};
