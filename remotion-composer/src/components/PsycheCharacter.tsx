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

const POSITIONS: Record<PsychePosition, React.CSSProperties> = {
  left: { left: "5%", transform: "translateX(0)" },
  center: { left: "50%", transform: "translateX(-50%)" },
  right: { right: "5%", left: "auto", transform: "translateX(0)" },
};

// ---- Sub-components ----

function Hair() {
  return (
    <>
      <path d="M 68 40 Q 75 20 100 18 Q 125 20 132 40" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <path d="M 72 35 Q 80 22 100 20 Q 120 22 128 35" stroke={STROKE} strokeWidth={2} fill="none" opacity={0.3} strokeLinecap="round" />
      <path d="M 100 18 L 100 10" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" opacity={0.5} />
    </>
  );
}

function Head() {
  return (
    <>
      <circle cx={100} cy={72} r={35} fill="#FFF8F2" stroke={STROKE} strokeWidth={STROKE_W} />
      {/* blush */}
      <circle cx={75} cy={78} r={5} fill="#FFB5B5" opacity={0.25} />
      <circle cx={125} cy={78} r={5} fill="#FFB5B5" opacity={0.25} />
    </>
  );
}

function LeftEye() {
  return <circle cx={85} cy={66} r={3.5} fill={STROKE} />;
}

function RightEye() {
  return <circle cx={115} cy={66} r={3.5} fill={STROKE} />;
}

function EyesShocked() {
  return (
    <>
      <circle cx={85} cy={66} r={5} fill="#FFF8F2" stroke={STROKE} strokeWidth={2} />
      <circle cx={85} cy={66} r={2.5} fill={STROKE} />
      <circle cx={115} cy={66} r={5} fill="#FFF8F2" stroke={STROKE} strokeWidth={2} />
      <circle cx={115} cy={66} r={2.5} fill={STROKE} />
    </>
  );
}

function EyesHappy() {
  return (
    <>
      <path d="M 82 66 Q 85 63 88 66" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />
      <path d="M 112 66 Q 115 63 118 66" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />
    </>
  );
}

function LeftEyebrow({ offsetY = 0, tilt = 0 }: { offsetY?: number; tilt?: number }) {
  const by = 51 - offsetY;
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
  const by = 51 - offsetY;
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
  return <path d="M 75 53 Q 85 57 95 55" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightEyebrowSad() {
  return <path d="M 105 55 Q 115 57 125 53" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightEyebrowFurrowed() {
  return <path d="M 105 53 Q 115 57 125 55" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

export function MouthNeutral() {
  return <path d="M 90 87 Q 100 90 110 87" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

export function MouthCurious() {
  return <path d="M 90 89 Q 100 95 110 89" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

export function MouthShocked() {
  return <ellipse cx={100} cy={90} rx={7} ry={9} stroke={STROKE} strokeWidth={2.5} fill="#FFF8F2" />;
}

export function MouthThinking() {
  return <path d="M 92 88 L 108 88" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

export function MouthSad() {
  return <path d="M 90 87 Q 100 82 110 87" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />;
}

export function MouthConfident() {
  return (
    <path d="M 87 85 Q 95 92 100 88 Q 105 92 113 85" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />
  );
}

export function MouthScared() {
  return (
    <path d="M 88 87 Q 100 98 112 87" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" opacity={0.6} />
  );
}

export function MouthHappy() {
  return (
    <path d="M 88 86 Q 100 96 112 86" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />
  );
}

function Body() {
  return (
    <>
      {/* neck */}
      <line x1={100} y1={105} x2={100} y2={115} stroke={STROKE} strokeWidth={STROKE_W} strokeLinecap="round" />
      {/* torso */}
      <path d="M 85 115 Q 100 120 115 115 L 115 195 Q 100 200 85 195 Z" fill="#FFF8F2" stroke={STROKE} strokeWidth={STROKE_W} strokeLinejoin="round" />
    </>
  );
}

function LeftArm({ raised = false }: { raised?: boolean }) {
  if (raised) {
    return <path d="M 90 130 L 60 95" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
  }
  return <path d="M 90 130 L 65 170" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightArm({ raised = false }: { raised?: boolean }) {
  if (raised) {
    return <path d="M 110 130 L 140 95" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
  }
  return <path d="M 110 130 L 135 170" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />;
}

function RightArmPointUp() {
  return (
    <>
      <path d="M 110 130 L 140 100 L 150 85" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <circle cx={150} cy={85} r={4} fill={STROKE} />
    </>
  );
}

function Legs() {
  return (
    <>
      <path d="M 95 195 L 70 255" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <path d="M 105 195 L 130 255" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      {/* shoes */}
      <ellipse cx={68} cy={258} rx={8} ry={4} fill={STROKE} />
      <ellipse cx={132} cy={258} rx={8} ry={4} fill={STROKE} />
    </>
  );
}

function HandOnChin() {
  return (
    <g>
      <path d="M 110 130 Q 145 120 155 130" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <circle cx={155} cy={130} r={5} fill={STROKE} />
    </g>
  );
}

function ArmsConfident() {
  return (
    <>
      <path d="M 88 130 L 50 150" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      <path d="M 112 130 L 150 150" stroke={STROKE} strokeWidth={STROKE_W} fill="none" strokeLinecap="round" />
      {/* hands on hips */}
      <circle cx={50} cy={150} r={4} fill={STROKE} />
      <circle cx={150} cy={150} r={4} fill={STROKE} />
    </>
  );
}

function HandsDown() {
  return (
    <>
      <circle cx={63} cy={172} r={4} fill={STROKE} />
      <circle cx={137} cy={172} r={4} fill={STROKE} />
    </>
  );
}

function Teardrop() {
  return (
    <path
      d="M 68 70 Q 70 78 68 84"
      stroke={STROKE}
      strokeWidth={2}
      fill="none"
      strokeLinecap="round"
      opacity={0.5}
    />
  );
}

// ---- Main component ----

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
    offsetY = Math.sin((frame * Math.PI * 2) / 45) * 0.8;
  } else if (animation === "point_up") {
    const p = Math.min(1, frame / 10);
    offsetY = -p * 5;
  }

  if (expression === "curious") {
    tiltDeg = 8;
  } else if (expression === "confused") {
    tiltDeg = -5;
  }

  const headTiltTransform = tiltDeg ? `rotate(${tiltDeg}, 100, 72)` : undefined;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: 70,
          width: size,
          height: size * 1.35,
          ...POSITIONS[position],
          transform: `translateX(${offsetX}px) translateY(${offsetY}px)`,
        }}
      >
        <svg
          viewBox="0 0 200 280"
          width={size}
          height={size * 1.35}
          xmlns="http://www.w3.org/2000/svg"
          style={headTiltTransform ? { transform: headTiltTransform } : undefined}
        >
          {/* Express layers */}
          <Hair />
          <Head />

          {/* Eyes */}
          {expression === "shocked" || expression === "scared" ? (
            <EyesShocked />
          ) : expression === "confident" ? (
            <EyesHappy />
          ) : (
            <>
              <LeftEye />
              <RightEye />
            </>
          )}

          {/* Eyebrows */}
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
              <LeftEyebrow offsetY={7} />
              <RightEyebrow offsetY={7} />
            </>
          ) : expression === "scared" ? (
            <>
              <LeftEyebrow offsetY={5} tilt={3} />
              <RightEyebrow offsetY={5} tilt={-3} />
            </>
          ) : expression === "confident" ? (
            <>
              <LeftEyebrow offsetY={-1} />
              <RightEyebrow offsetY={-1} />
            </>
          ) : expression === "curious" ? (
            <>
              <LeftEyebrow offsetY={6} />
              <RightEyebrow offsetY={1} />
            </>
          ) : expression === "confused" ? (
            <>
              <LeftEyebrow offsetY={-2} tilt={4} />
              <RightEyebrow offsetY={6} tilt={-3} />
            </>
          ) : (
            <>
              <LeftEyebrow offsetY={0} />
              <RightEyebrow offsetY={0} />
            </>
          )}

          {/* Mouth */}
          {expression === "neutral" && <MouthNeutral />}
          {expression === "curious" && <MouthCurious />}
          {expression === "shocked" && <MouthShocked />}
          {expression === "thinking" && <MouthThinking />}
          {expression === "sad" && <MouthSad />}
          {expression === "confident" && <MouthConfident />}
          {expression === "scared" && <MouthScared />}
          {expression === "confused" && <MouthCurious />}

          {/* Body */}
          <Body />

          {/* Arms */}
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
              <HandsDown />
            </>
          )}

          <Legs />
          {expression === "sad" && <Teardrop />}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
