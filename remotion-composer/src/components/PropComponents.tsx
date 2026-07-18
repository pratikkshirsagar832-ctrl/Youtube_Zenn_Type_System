import React from "react";

const S = "#1A1A1A";
const W = 3;

interface PropBase {
  size?: number;
}

export const SkullProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <circle cx={50} cy={40} r={30} fill="#FFF8F2" stroke={S} strokeWidth={W} />
    <circle cx={35} cy={35} r={5} fill={S} />
    <circle cx={65} cy={35} r={5} fill={S} />
    <path d="M 40 52 Q 50 60 60 52" stroke={S} strokeWidth={2.5} fill="none" strokeLinecap="round" />
    <path d="M 45 48 L 45 55" stroke={S} strokeWidth={2} opacity={0.3} />
    <path d="M 55 48 L 55 55" stroke={S} strokeWidth={2} opacity={0.3} />
    <rect x={38} y={65} width={24} height={30} rx={4} fill="#FFF8F2" stroke={S} strokeWidth={W} />
    <line x1={45} y1={72} x2={45} y2={90} stroke={S} strokeWidth={2} />
    <line x1={55} y1={72} x2={55} y2={90} stroke={S} strokeWidth={2} />
    <line x1={42} y1={95} x2={58} y2={95} stroke={S} strokeWidth={2} />
  </svg>
);

export const FireProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <path d="M 50 15 Q 65 35 60 55 Q 55 70 50 80 Q 45 70 40 55 Q 35 35 50 15 Z" fill="#FF6B35" stroke={S} strokeWidth={W} strokeLinejoin="round" />
    <path d="M 50 25 Q 58 40 55 50 Q 52 60 50 65 Q 48 60 45 50 Q 42 40 50 25 Z" fill="#FFD700" opacity={0.7} />
    <path d="M 40 80 Q 35 95 50 100 Q 65 95 60 80" fill="none" stroke={S} strokeWidth={W} strokeLinecap="round" />
    <path d="M 30 85 Q 25 92 35 98" stroke={S} strokeWidth={2} fill="none" strokeLinecap="round" opacity={0.4} />
    <path d="M 70 85 Q 75 92 65 98" stroke={S} strokeWidth={2} fill="none" strokeLinecap="round" opacity={0.4} />
  </svg>
);

export const BrainProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M 30 45 Q 25 20 45 15 Q 55 12 60 18 Q 65 12 75 15 Q 85 20 80 45" fill="#FFF0E0" stroke={S} strokeWidth={W} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M 30 45 Q 20 55 25 65 Q 30 75 45 75" fill="#FFF0E0" stroke={S} strokeWidth={W} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M 80 45 Q 90 55 85 65 Q 80 75 65 75" fill="#FFF0E0" stroke={S} strokeWidth={W} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M 45 75 Q 50 85 65 75" fill="#FFF0E0" stroke={S} strokeWidth={W} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M 40 40 Q 50 30 60 40 Q 50 50 40 40" fill="none" stroke={S} strokeWidth={2} opacity={0.3} />
    <path d="M 45 50 Q 55 45 65 55" stroke={S} strokeWidth={2} fill="none" opacity={0.3} />
  </svg>
);

export const ClockProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <circle cx={50} cy={45} r={30} fill="#FFF8F2" stroke={S} strokeWidth={W} />
    <circle cx={50} cy={45} r={2} fill={S} />
    <line x1={50} y1={45} x2={50} y2={25} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={50} y1={45} x2={68} y2={50} stroke={S} strokeWidth={2.5} strokeLinecap="round" />
    <circle cx={50} cy={45} r={26} fill="none" stroke={S} strokeWidth={1} opacity={0.3} />
    {/* stand */}
    <line x1={50} y1={75} x2={50} y2={100} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={30} y1={110} x2={70} y2={110} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={40} y1={100} x2={30} y2={110} stroke={S} strokeWidth={2.5} strokeLinecap="round" />
    <line x1={60} y1={100} x2={70} y2={110} stroke={S} strokeWidth={2.5} strokeLinecap="round" />
  </svg>
);

export const HeartProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M 50 85 C 15 55 15 25 35 18 C 45 14 50 22 50 30 C 50 22 55 14 65 18 C 85 25 85 55 50 85 Z" fill="#FF6B6B" stroke={S} strokeWidth={W} strokeLinejoin="round" />
    <path d="M 40 32 Q 50 28 60 32" stroke="#FFF" strokeWidth={2} fill="none" opacity={0.4} strokeLinecap="round" />
  </svg>
);

export const QuestionMarkProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <path d="M 50 5 L 70 15 L 65 40 L 50 45" fill="none" stroke={S} strokeWidth={W} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M 50 45 L 50 60" stroke={S} strokeWidth={W} strokeLinecap="round" />
    <circle cx={50} cy={78} r={5} fill={S} />
  </svg>
);

export const BookProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <rect x={20} y={15} width={60} height={85} rx={4} fill="#FFF8F2" stroke={S} strokeWidth={W} />
    <line x1={50} y1={15} x2={50} y2={100} stroke={S} strokeWidth={W} />
    <rect x={25} y={25} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
    <rect x={55} y={25} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
    <rect x={25} y={40} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
    <rect x={55} y={40} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
    <rect x={25} y={55} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
    <rect x={55} y={55} width={20} height={8} rx={2} fill="none" stroke={S} strokeWidth={2} opacity={0.2} />
  </svg>
);

export const MirrorProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx={50} cy={40} rx={25} ry={32} fill="#D4E8F0" stroke={S} strokeWidth={W} />
    <ellipse cx={50} cy={40} rx={22} ry={29} fill="none" stroke={S} strokeWidth={1} opacity={0.3} />
    <line x1={50} y1={72} x2={50} y2={100} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={35} y1={110} x2={65} y2={110} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={42} y1={100} x2={35} y2={110} stroke={S} strokeWidth={2.5} strokeLinecap="round" />
    <line x1={58} y1={100} x2={65} y2={110} stroke={S} strokeWidth={2.5} strokeLinecap="round" />
  </svg>
);

export const ChainProp: React.FC<PropBase> = ({ size = 70 }) => (
  <svg width={size} height={size} viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
    <line x1={30} y1={20} x2={70} y2={100} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <line x1={40} y1={20} x2={80} y2={100} stroke={S} strokeWidth={3} strokeLinecap="round" />
    <circle cx={50} cy={30} r={6} fill="none" stroke={S} strokeWidth={3} />
    <circle cx={55} cy={50} r={6} fill="none" stroke={S} strokeWidth={3} />
    <circle cx={60} cy={70} r={6} fill="none" stroke={S} strokeWidth={3} />
    <circle cx={65} cy={90} r={6} fill="none" stroke={S} strokeWidth={3} />
  </svg>
);

export const propComponents: Record<string, React.FC<PropBase>> = {
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
