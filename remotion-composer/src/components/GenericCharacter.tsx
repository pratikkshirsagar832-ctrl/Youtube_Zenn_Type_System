import React from "react";

const STROKE = "#1A1A1A";
const SW = 3;

interface GenericCharacterProps {
  position?: "left" | "right";
  size?: number;
}

export const GenericCharacter: React.FC<GenericCharacterProps> = ({ position = "left", size = 220 }) => {
  const posStyle: React.CSSProperties =
    position === "left"
      ? { left: "5%", transform: "translateX(0)" }
      : { right: "5%", left: "auto", transform: "translateX(0)" };

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        width: size,
        height: size * 1.3,
        ...posStyle,
      }}
    >
      <svg viewBox="0 0 200 280" width={size} height={size * 1.3} xmlns="http://www.w3.org/2000/svg">
        <circle cx={100} cy={65} r={35} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
        <circle cx={85} cy={60} r={3} fill={STROKE} />
        <circle cx={115} cy={60} r={3} fill={STROKE} />
        <path d="M 78 46 Q 85 42 92 46" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
        <path d="M 108 46 Q 115 44 122 46" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
        <path d="M 92 82 Q 100 86 108 82" stroke={STROKE} strokeWidth={2.5} fill="none" strokeLinecap="round" />
        <line x1={100} y1={100} x2={100} y2={200} stroke={STROKE} strokeWidth={SW} strokeLinecap="round" />
        <path d="M 100 130 L 70 170" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
        <path d="M 100 130 L 130 170" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
        <path d="M 100 200 L 75 250" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
        <path d="M 100 200 L 125 250" stroke={STROKE} strokeWidth={SW} fill="none" strokeLinecap="round" />
      </svg>
    </div>
  );
};
