import React from "react";
import { AbsoluteFill } from "remotion";

// ---------------------------------------------------------------------------
// Psyche — Nexus character
// LOCKED visual identity:
//   - Asymmetric eyes (left narrow, right wide)
//   - Left eyebrow ALWAYS raised
//   - Single color: white normally, gold when highlighted
//   - 7 expression variants
// ---------------------------------------------------------------------------

export type PsycheExpression =
  | "default"
  | "shocked"
  | "thinking"
  | "explaining"
  | "scared"
  | "concerned"
  | "knowing";

export type PsychePosition = "center" | "left" | "right";

export interface PsycheCharacterProps {
  expression: PsycheExpression;
  highlightedWord?: string;
  position?: PsychePosition;
  size?: number; // default 400
}

const POSITION_STYLES: Record<PsychePosition, React.CSSProperties> = {
  center: { left: "50%", transform: "translateX(-50%)" },
  left: { left: "8%" },
  right: { right: "8%" },
};

function EyeLeft({ y, fill }: { y: number; fill: string }) {
  // Narrow slit eye
  return (
    <rect x="58" y={y} width="22" height="6" rx="3" fill={fill} />
  );
}

function EyeRight({ y, fill }: { y: number; fill: string }) {
  // Wide round eye
  return (
    <circle cx="142" cy={y + 6} r="10" fill={fill} />
  );
}

function LeftEyebrow({ raised, fill }: { raised: number; fill: string }) {
  // Always raised by `raised` px above default. raised=4 for normal, raised=10 for "knowing".
  return (
    <path
      d={`M 50 ${30 - raised} Q 70 ${22 - raised} 92 ${30 - raised}`}
      stroke={fill}
      strokeWidth={4}
      fill="none"
      strokeLinecap="round"
    />
  );
}

function RightEyebrow({ expression, fill }: { expression: PsycheExpression; fill: string }) {
  // Right eyebrow varies by expression.
  const baseY = 30;
  switch (expression) {
    case "shocked":
      return <path d={`M 110 ${baseY - 14} Q 135 ${baseY - 20} 165 ${baseY - 14}`} stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "scared":
      return <path d={`M 110 ${baseY - 12} Q 135 ${baseY - 6} 165 ${baseY - 12}`} stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "concerned":
      return <path d={`M 110 ${baseY - 4} Q 135 ${baseY - 8} 165 ${baseY - 4}`} stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "knowing":
      return <path d={`M 110 ${baseY} Q 135 ${baseY - 4} 165 ${baseY}`} stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "thinking":
    case "explaining":
    case "default":
    default:
      return <path d={`M 110 ${baseY - 4} Q 135 ${baseY - 8} 165 ${baseY - 4}`} stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
  }
}

function Mouth({ expression, fill }: { expression: PsycheExpression; fill: string }) {
  switch (expression) {
    case "shocked":
      return <ellipse cx="105" cy="125" rx="14" ry="18" fill={fill} />;
    case "scared":
      return <path d="M 88 128 Q 105 138 122 128" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "concerned":
      return <path d="M 88 132 Q 105 124 122 132" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "knowing":
      return <path d="M 88 122 Q 105 130 122 122" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "thinking":
      return <path d="M 88 128 L 122 128" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "explaining":
      return <path d="M 88 120 Q 105 128 122 120" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "default":
    default:
      return <path d="M 92 124 Q 105 128 118 124" stroke={fill} strokeWidth={4} fill="none" strokeLinecap="round" />;
  }
}

function HandOnChin({ fill }: { fill: string }) {
  return (
    <g>
      <path d="M 130 130 Q 145 120 155 130" stroke={fill} strokeWidth={5} fill="none" strokeLinecap="round" />
      <circle cx="155" cy="130" r="6" fill={fill} />
    </g>
  );
}

function HandsExplaining({ fill }: { fill: string }) {
  return (
    <g>
      <path d="M 60 140 Q 45 130 35 145" stroke={fill} strokeWidth={5} fill="none" strokeLinecap="round" />
      <path d="M 150 140 Q 165 130 175 145" stroke={fill} strokeWidth={5} fill="none" strokeLinecap="round" />
    </g>
  );
}

export const PsycheCharacter: React.FC<PsycheCharacterProps> = ({
  expression,
  highlightedWord,
  position = "center",
  size = 400,
}) => {
  const isHighlighted = !!highlightedWord;
  const fill = isHighlighted ? "#F4D03F" : "#FFFFFF";

  const leftBrowRaised = expression === "knowing" ? 10 : 4;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: 80,
          width: size,
          height: size,
          ...POSITION_STYLES[position],
        }}
      >
        <svg
          viewBox="0 0 210 200"
          width={size}
          height={size}
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Head outline */}
          <ellipse
            cx="105"
            cy="100"
            rx="75"
            ry="85"
            fill="none"
            stroke={fill}
            strokeWidth={3}
          />

          {/* Eyes */}
          <EyeLeft y={70} fill={fill} />
          <EyeRight y={70} fill={fill} />

          {/* Eyebrows */}
          <LeftEyebrow raised={leftBrowRaised} fill={fill} />
          <RightEyebrow expression={expression} fill={fill} />

          {/* Mouth */}
          <Mouth expression={expression} fill={fill} />

          {/* Expression-specific overlays */}
          {expression === "thinking" && <HandOnChin fill={fill} />}
          {expression === "explaining" && <HandsExplaining fill={fill} />}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
