import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export type PsycheExpression =
  | "neutral"
  | "curious"
  | "shocked"
  | "thinking"
  | "sad"
  | "confident"
  | "scared"
  | "confused";

export type PsychePosition = "left" | "center" | "right";
export type PsycheAnimation = "idle" | "walk_in_left" | "walk_in_right" | "walk_out_left" | "point_up";

export interface PsycheCharacterProps {
  expression: PsycheExpression;
  position?: PsychePosition;
  animation?: PsycheAnimation;
  size?: number;
}

const STROKE = "#1A1A1A";
const STROKE_W = 3;
const FACE_FILL = "#FFFFFF";

const POSITIONS: Record<PsychePosition, React.CSSProperties> = {
  left: { left: "5%", transform: "translateX(0)" },
  center: { left: "50%", transform: "translateX(-50%)" },
  right: { right: "5%", left: "auto", transform: "translateX(0)" },
};

function Head() {
  return <circle cx={100} cy={65} r={35} fill={FACE_FILL} stroke={STROKE} strokeWidth={STROKE_W} />;
}

function LeftEye() {
  return <circle cx={85} cy={60} r={3} fill={STROKE} />;
}

function RightEye() {
  return <circle cx={115} cy={60} r={3} fill={STROKE} />;
}

function EyesShocked() {
  return <circle cx={115} cy={60} r={4.5} fill={STROKE} />;
}

function LeftEyebrow({ offsetY = 0, tilt = 0 }: { offsetY?: number; tilt?: number }) {
  const by = 46 - offsetY;
  const t = tilt;
  return (
    <path
      d={`M 75 ${by + t} Q 85 ${by - 4 - t} 95 ${by - t}`}
      stroke={STROKE}
      strokeWidth={STROKE_W}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function RightEyebrow({ offsetY = 0, tilt = 0 }: { offsetY?: number; tilt?: number }) {
  const by = 46 - offsetY;
  const t = tilt;
  return (
    <path
      d={`M 105 ${by - t} Q 115 ${by - 4 + t} 125 ${by + t}`}
      stroke={STROKE}
      strokeWidth={STROKE_W}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function LeftEyebrowSad() {
  return (
    <path
      d="M 75 48 Q 85 52 95 50"
      stroke={STROKE}
      strokeWidth={STROKE_W}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function RightEyebrowSad() {
  return (
    <path
      d="M 105 50 Q 115 52 125 48"
      stroke={STROKE}
      strokeWidth={STROKE_W}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function RightEyebrowFurrowed() {
  return (
    <path
      d="M 105 48 Q 115 52 125 50"
      stroke={STROKE}
      strokeWidth={STROKE_W}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function MouthNeutral() {
  return <path d="M 90 80 Q 100 83 110 80" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function MouthCurious() {
  return <path d="M 90 82 Q 100 88 110 82" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function MouthShocked() {
  return <ellipse cx={100} cy={82} rx={6} ry={8} stroke={STROKE} strokeWidth={2.5} fill="none" />;
}

function MouthThinking() {
  return <path d="M 92 80 L 108 80" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function MouthSad() {
  return <path d="M 90 80 Q 100 75 110 80" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function MouthConfident() {
  return <path d="M 88 78 Q 100 88 112 78" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function MouthScared() {
  return <path d="M 88 80 Q 100 90 112 80" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

function Body() {
  return <line x1={100} y1={100} x2={100} y2={200} stroke={STROKE} strokeWidth={STROKE_W} strokeLinecap="round" />;
}

function LeftArm({ raised = false }: { raised?: boolean }) {
  if (raised) {
    return <path d="M 100 130 L 65 100" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
  }
  return <path d="M 100 130 L 70 170" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightArm({ raised = false }: { raised?: boolean }) {
  if (raised) {
    return <path d="M 100 130 L 135 100" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
  }
  return <path d="M 100 130 L 130 170" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightArmExplaining() {
  return (
    <path d="M 100 130 Q 140 120 155 140" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
  );
}

function RightArmPointUp() {
  return (
    <path d="M 100 130 L 140 100 L 150 85" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
  );
}

function Legs() {
  return (
    <>
      <path d="M 100 200 L 75 250" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <path d="M 100 200 L 125 250" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
    </>
  );
}

function HandOnChin() {
  return (
    <g>
      <path d="M 130 130 Q 145 120 155 130" stroke={STROKE} strokeWidth={3} fill="none" strokeLinecap="round" />
      <circle cx={155} cy={130} r={5} fill={STROKE} />
    </g>
  );
}

function ArmsConfident() {
  return (
    <>
      <path d="M 100 130 L 55 150" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <path d="M 100 130 L 145 150" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
    </>
  );
}

function Teardrop() {
  return (
    <path
      d="M 70 65 Q 72 72 70 78"
      stroke={STROKE}
      strokeWidth={2}
      fill="none"
      strokeLinecap="round"
      opacity={0.6}
    />
  );
}

export const PsycheCharacter: React.FC<PsycheCharacterProps> = ({
  expression,
  position = "center",
  animation = "idle",
  size = 250,
}) => {
  const frame = useCurrentFrame();

  let offsetX = 0;
  let offsetY = 0;
  let tiltDeg = 0;

  if (animation === "walk_in_left") {
    offsetX = interpolate(frame, [0, 20], [-400, 0], { extrapolateRight: "clamp" });
  } else if (animation === "walk_in_right") {
    offsetX = interpolate(frame, [0, 20], [400, 0], { extrapolateRight: "clamp" });
  } else if (animation === "walk_out_left") {
    offsetX = interpolate(frame, [0, 20], [0, -400], { extrapolateLeft: "clamp" });
  } else if (animation === "idle") {
    offsetY = Math.sin((frame * Math.PI * 2) / 60) * 0.5;
  } else if (animation === "point_up") {
    const p = Math.min(1, frame / 10);
    offsetY = -p * 5;
  }

  if (expression === "curious") {
    tiltDeg = 8;
  }

  const headTiltTransform = tiltDeg ? `rotate(${tiltDeg}, 100, 65)` : undefined;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: 80,
          width: size,
          height: size * 1.3,
          ...POSITIONS[position],
          transform: `translateX(${offsetX}px) translateY(${offsetY}px)`,
        }}
      >
        <svg
          viewBox="0 0 200 280"
          width={size}
          height={size * 1.3}
          xmlns="http://www.w3.org/2000/svg"
          style={headTiltTransform ? { transform: headTiltTransform } : undefined}
        >
          <Head />
          <LeftEye />
          {expression === "shocked" || expression === "scared" ? (
            <EyesShocked />
          ) : (
            <RightEye />
          )}

          {expression === "sad" ? (
            <>
              <LeftEyebrowSad />
              <RightEyebrowSad />
            </>
          ) : expression === "thinking" ? (
            <>
              <LeftEyebrow offsetY={4} />
              <RightEyebrowFurrowed />
            </>
          ) : expression === "shocked" ? (
            <>
              <LeftEyebrow offsetY={6} />
              <RightEyebrow offsetY={6} />
            </>
          ) : expression === "scared" ? (
            <>
              <LeftEyebrow offsetY={5} tilt={2} />
              <RightEyebrow offsetY={5} tilt={-2} />
            </>
          ) : expression === "confident" ? (
            <>
              <LeftEyebrow offsetY={0} />
              <RightEyebrow offsetY={0} />
            </>
          ) : expression === "curious" ? (
            <>
              <LeftEyebrow offsetY={5} />
              <RightEyebrow offsetY={0} />
            </>
          ) : expression === "confused" ? (
            <>
              <LeftEyebrow offsetY={-3} tilt={3} />
              <RightEyebrow offsetY={5} tilt={-2} />
            </>
          ) : (
            <>
              <LeftEyebrow offsetY={0} />
              <RightEyebrow offsetY={0} />
            </>
          )}

          {expression === "neutral" && <MouthNeutral />}
          {expression === "curious" && <MouthCurious />}
          {expression === "shocked" && <MouthShocked />}
          {expression === "thinking" && <MouthThinking />}
          {expression === "sad" && <MouthSad />}
          {expression === "confident" && <MouthConfident />}
          {expression === "scared" && <MouthScared />}
          {expression === "confused" && <MouthThinking />}

          <Body />
          <Legs />

          {expression === "scared" ? (
            <>
              <LeftArm raised={true} />
              <RightArm raised={true} />
            </>
          ) : expression === "confident" ? (
            <ArmsConfident />
          ) : expression === "thinking" ? (
            <>
              <LeftArm />
              <RightArm />
              <HandOnChin />
            </>
          ) : animation === "point_up" ? (
            <>
              <LeftArm />
              <RightArmPointUp />
            </>
          ) : (
            <>
              <LeftArm />
              <RightArm />
            </>
          )}

          {expression === "sad" && <Teardrop />}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
