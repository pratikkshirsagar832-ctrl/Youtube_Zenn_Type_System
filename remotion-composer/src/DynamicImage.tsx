import React from "react";
import { useCurrentFrame, staticFile } from "remotion";

// ---------------------------------------------------------------------------
// DynamicImage — Ken Burns motion locked to 6 types
// LOCKED transform values (from PLAN.md §8.1):
//   zoom_in_slow:   scale 1.0 -> 1.2
//   zoom_out_fast:  scale 1.3 -> 1.0
//   pan_left:       scale 1.1, translateX 0% -> -10%
//   pan_right:      scale 1.1, translateX 0% -> +10%
//   fade_in:        opacity 0 -> 1
//   static:         scale 1.0, translateX 0
// ---------------------------------------------------------------------------

export type MotionType =
  | "zoom_in_slow"
  | "zoom_out_fast"
  | "pan_left"
  | "pan_right"
  | "fade_in"
  | "static";

export interface DynamicImageProps {
  imagePath: string;
  motionType: MotionType;
  durationInFrames: number;
  backgroundColor?: string;
}

export const DynamicImage: React.FC<DynamicImageProps> = ({
  imagePath,
  motionType,
  durationInFrames,
  backgroundColor = "#0A0A0F",
}) => {
  const frame = useCurrentFrame();
  const progress = Math.min(1, Math.max(0, frame / Math.max(1, durationInFrames)));

  const transforms: Record<MotionType, { scale: number; translateX: string; opacity: number }> = {
    zoom_in_slow: { scale: 1.0 + 0.2 * progress, translateX: "0%", opacity: 1 },
    zoom_out_fast: { scale: 1.3 - 0.3 * progress, translateX: "0%", opacity: 1 },
    pan_left: { scale: 1.1, translateX: `${-10 * progress}%`, opacity: 1 },
    pan_right: { scale: 1.1, translateX: `${10 * progress}%`, opacity: 1 },
    fade_in: { scale: 1.0, translateX: "0%", opacity: progress },
    static: { scale: 1.0, translateX: "0%", opacity: 1 },
  };

  const { scale, translateX, opacity } = transforms[motionType] ?? transforms.static;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `url(${staticFile(imagePath)})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          transform: `scale(${scale}) translateX(${translateX})`,
          opacity,
          willChange: "transform, opacity",
        }}
      />
    </div>
  );
};
