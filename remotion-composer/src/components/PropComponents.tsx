import React from "react";

const STROKE = "#1A1A1A";
const SW = 3;

export const SkullProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <circle cx={30} cy={26} r={18} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <rect x={22} y={38} width={16} height={10} rx={3} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <circle cx={24} cy={24} r={3} fill={STROKE} />
    <circle cx={36} cy={24} r={3} fill={STROKE} />
    <path d="M 27 32 L 33 32" stroke={STROKE} strokeWidth={2} strokeLinecap="round" />
    <line x1={26} y1={44} x2={34} y2={44} stroke={STROKE} strokeWidth={1.5} />
  </svg>
);

export const FireProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <path
      d="M 30 55 C 22 44 18 36 22 26 C 26 18 30 10 30 5 C 30 10 34 18 38 26 C 42 36 38 44 30 55Z"
      fill="#FF6B35"
      stroke="#D64520"
      strokeWidth={2}
      opacity={0.9}
    />
    <path
      d="M 30 50 C 25 42 23 36 26 30 C 28 26 30 20 30 15 C 30 20 32 26 34 30 C 37 36 35 42 30 50Z"
      fill="#FFD700"
      opacity={0.7}
    />
  </svg>
);

export const BrainProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <ellipse cx={25} cy={28} rx={14} ry={10} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <ellipse cx={35} cy={28} rx={14} ry={10} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <path d="M 25 28 Q 30 34 35 28" stroke={STROKE} strokeWidth={1.5} fill="none" />
    <path d="M 18 28 Q 12 22 18 18" stroke={STROKE} strokeWidth={1.5} fill="none" />
    <path d="M 42 28 Q 48 22 42 18" stroke={STROKE} strokeWidth={1.5} fill="none" />
    <path d="M 25 22 Q 20 15 28 14" stroke={STROKE} strokeWidth={1.5} fill="none" />
    <path d="M 35 22 Q 40 15 32 14" stroke={STROKE} strokeWidth={1.5} fill="none" />
  </svg>
);

export const ClockProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <circle cx={30} cy={30} r={22} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <line x1={30} y1={30} x2={30} y2={16} stroke={STROKE} strokeWidth={2.5} strokeLinecap="round" />
    <line x1={30} y1={30} x2={40} y2={34} stroke={STROKE} strokeWidth={2.5} strokeLinecap="round" />
    <circle cx={30} cy={30} r={2.5} fill={STROKE} />
  </svg>
);

export const HeartProp: React.FC<{ size?: number }> = ({ size = 50 }) => (
  <svg width={size} height={size} viewBox="0 0 50 50">
    <path
      d="M 25 42 C 10 30 5 20 10 13 C 14 7 22 7 25 14 C 28 7 36 7 40 13 C 45 20 40 30 25 42Z"
      fill="#FFFFFF"
      stroke={STROKE}
      strokeWidth={SW}
    />
  </svg>
);

export const QuestionMarkProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <text
      x={30} y={48}
      textAnchor="middle"
      fontSize={52}
      fontWeight="bold"
      fill={STROKE}
      fontFamily="Arial, sans-serif"
    >
      ?
    </text>
  </svg>
);

export const BookProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <rect x={10} y={10} width={40} height={38} rx={2} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <line x1={30} y1={10} x2={30} y2={48} stroke={STROKE} strokeWidth={SW} />
    <line x1={16} y1={20} x2={26} y2={20} stroke={STROKE} strokeWidth={1.5} />
    <line x1={16} y1={28} x2={26} y2={28} stroke={STROKE} strokeWidth={1.5} />
    <line x1={16} y1={36} x2={26} y2={36} stroke={STROKE} strokeWidth={1.5} />
    <line x1={34} y1={20} x2={44} y2={20} stroke={STROKE} strokeWidth={1.5} />
    <line x1={34} y1={28} x2={44} y2={28} stroke={STROKE} strokeWidth={1.5} />
    <line x1={34} y1={36} x2={44} y2={36} stroke={STROKE} strokeWidth={1.5} />
  </svg>
);

export const MirrorProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <ellipse cx={30} cy={24} rx={16} ry={20} fill="#FFFFFF" stroke={STROKE} strokeWidth={SW} />
    <line x1={30} y1={44} x2={30} y2={56} stroke={STROKE} strokeWidth={SW} strokeLinecap="round" />
  </svg>
);

export const ChainProp: React.FC<{ size?: number }> = ({ size = 60 }) => (
  <svg width={size} height={size} viewBox="0 0 60 60">
    <ellipse cx={22} cy={30} rx={8} ry={12} fill="none" stroke={STROKE} strokeWidth={SW} />
    <ellipse cx={38} cy={30} rx={8} ry={12} fill="none" stroke={STROKE} strokeWidth={SW} />
    <line x1={28} y1={22} x2={32} y2={22} stroke={STROKE} strokeWidth={SW} />
    <line x1={28} y1={38} x2={32} y2={38} stroke={STROKE} strokeWidth={SW} />
  </svg>
);

export const propComponents: Record<string, React.FC<{ size?: number }>> = {
  SkullProp,
  FireProp,
  BrainProp,
  ClockProp,
  HeartProp,
  QuestionMarkProp,
  BookProp,
  MirrorProp,
  ChainProp,
};
