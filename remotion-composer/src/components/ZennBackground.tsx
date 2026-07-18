import React from "react";

// Deterministic pseudo-random seeded by position for consistent wobble
function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

function wobbleOffset(seed: number, amplitude = 2): number {
  return (seededRandom(seed) - 0.5) * 2 * amplitude;
}

function wobblePath(x: number, y: number, w: number, h: number, wobble = 2): string {
  const s = Math.round(x + y * 1000 + w * 2000 + h * 3000);
  const o = (i: number) => wobbleOffset(s + i, wobble);
  const x1 = x + o(1);
  const y1 = y + o(2);
  const x2 = x + w + o(3);
  const y2 = y + o(4);
  const x3 = x + w + o(5);
  const y3 = y + h + o(6);
  const x4 = x + o(7);
  const y4 = y + h + o(8);
  const cpOff = (i: number) => wobbleOffset(s + 100 + i, wobble * 1.5);
  return (
    `M ${x1} ${y1} ` +
    `C ${x1 + w / 3 + cpOff(1)} ${y1 + cpOff(2)} ${x1 + (2 * w) / 3 + cpOff(3)} ${y2 + cpOff(4)} ${x2} ${y2} ` +
    `C ${x2 + cpOff(5)} ${y2 + h / 3 + cpOff(6)} ${x3 + cpOff(7)} ${y3 - h / 3 + cpOff(8)} ${x3} ${y3} ` +
    `C ${x3 - w / 3 + cpOff(9)} ${y3 + cpOff(10)} ${x4 + (2 * w) / 3 + cpOff(11)} ${y4 + cpOff(12)} ${x4} ${y4} ` +
    `C ${x4 + cpOff(13)} ${y4 - h / 3 + cpOff(14)} ${x1 + cpOff(15)} ${y1 + h / 3 + cpOff(16)} ${x1} ${y1}`
  );
}

function wobbleLine(x1: number, y1: number, x2: number, y2: number, wobble = 2): string {
  const s = Math.round(x1 + y1 * 1000 + x2 * 2000 + y2 * 3000);
  const cx1 = x1 + (x2 - x1) / 3;
  const cx2 = x1 + (2 * (x2 - x1)) / 3;
  const wy1 = y1 + wobbleOffset(s + 1, wobble);
  const wy2 = y2 + wobbleOffset(s + 2, wobble);
  return `M ${x1} ${y1} C ${cx1} ${wy1} ${cx2} ${wy2} ${x2} ${y2}`;
}

// Convert percent (0-100) to pixel for 1920x1080 canvas
const W = 1920;
const H = 1080;
const pctX = (p: number) => (p / 100) * W;
const pctY = (p: number) => (p / 100) * H;
const pctW = (p: number) => (p / 100) * W;
const pctH = (p: number) => (p / 100) * H;

export interface BackgroundElement {
  type: "rect" | "circle" | "text" | "line" | "path" | "polygon" | "timeline_bar" | "ground";
  label?: string;
  x_percent?: number;
  y_percent?: number;
  width_percent?: number;
  height_percent?: number;
  cx_percent?: number;
  cy_percent?: number;
  r_percent?: number;
  x1_percent?: number;
  y1_percent?: number;
  x2_percent?: number;
  y2_percent?: number;
  fill?: string;
  stroke?: string;
  stroke_width?: number;
  bg_fill?: string;
  content?: string;
  font_size?: number;
  font_family?: string;
  text_anchor?: string;
  fontWeight?: string;
  d?: string;
  points?: Array<{ x_percent: number; y_percent: number }>;
  fill_percent?: number;
  fill_color?: string;
  remaining_color?: string;
  year_label?: string;
  ground_color?: string;
  border_radius?: number;
  wobble?: boolean;
}

interface ZennBackgroundProps {
  bg_color: string;
  elements: BackgroundElement[];
}

const RectElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const x = pctX(el.x_percent ?? 0);
  const y = pctY(el.y_percent ?? 0);
  const w = pctW(el.width_percent ?? 0);
  const h = pctH(el.height_percent ?? 0);
  const wobble = el.wobble !== false;
  const strokeW = el.stroke_width ?? 0;
  if (wobble && strokeW > 0) {
    return (
      <path
        d={wobblePath(x, y, w, h)}
        fill={el.fill || "none"}
        stroke={el.stroke || "#1A1A1A"}
        strokeWidth={strokeW}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    );
  }
  return (
    <rect
      x={x} y={y} width={w} height={h}
      fill={el.fill || "none"}
      stroke={el.stroke || "none"}
      strokeWidth={strokeW}
      rx={el.border_radius ?? 0}
    />
  );
};

const CircleElement: React.FC<{ el: BackgroundElement }> = ({ el }) => (
  <circle
    cx={pctX(el.cx_percent ?? 0)}
    cy={pctY(el.cy_percent ?? 0)}
    r={pctW(el.r_percent ?? 0)}
    fill={el.fill || "none"}
    stroke={el.stroke || "none"}
    strokeWidth={el.stroke_width ?? 0}
  />
);

const TextElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const x = pctX(el.x_percent ?? 0);
  const y = pctY(el.y_percent ?? 0);
  const fontSize = el.font_size ?? 36;
  const anchor = el.text_anchor || "start";
  const font = el.font_family || "'Patrick Hand', cursive, sans-serif";

  return (
    <>
      {el.bg_fill && (
        <rect
          x={x - fontSize * 0.1}
          y={y - fontSize * 0.8}
          width={fontSize * (el.content?.length ?? 1) * 0.6 + fontSize * 0.2}
          height={fontSize * 1.2}
          rx={fontSize * 0.1}
          fill={el.bg_fill}
          stroke="#1A1A1A"
          strokeWidth={2}
        />
      )}
      <text
        x={x}
        y={y}
        fontSize={fontSize}
        fill={el.fill || "#1A1A1A"}
        fontFamily={font}
        fontWeight={el.fontWeight || "bold"}
        textAnchor={anchor as "start" | "middle" | "end"}
        dominantBaseline="central"
      >
        {el.content}
      </text>
    </>
  );
};

const LineElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const x1 = pctX(el.x1_percent ?? 0);
  const y1 = pctY(el.y1_percent ?? 0);
  const x2 = pctX(el.x2_percent ?? 0);
  const y2 = pctY(el.y2_percent ?? 0);
  const wobble = el.wobble !== false;
  const strokeW = el.stroke_width ?? 3;
  if (wobble) {
    return (
      <path
        d={wobbleLine(x1, y1, x2, y2)}
        stroke={el.stroke || "#1A1A1A"}
        strokeWidth={strokeW}
        fill="none"
        strokeLinecap="round"
      />
    );
  }
  return (
    <line
      x1={x1} y1={y1} x2={x2} y2={y2}
      stroke={el.stroke || "#1A1A1A"}
      strokeWidth={strokeW}
      strokeLinecap="round"
    />
  );
};

const PathElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  if (!el.d) return null;
  const scaled = el.d.replace(/([+-]?\d+\.?\d*)/g, (m) => {
    const n = parseFloat(m);
    if (n > 100) return String(n);
    return String(pctW(n));
  });
  return (
    <path
      d={scaled}
      fill={el.fill || "none"}
      stroke={el.stroke || "none"}
      strokeWidth={el.stroke_width ?? 0}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  );
};

const PolygonElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  if (!el.points || el.points.length < 2) return null;
  const pts = el.points.map((p) => `${pctX(p.x_percent)},${pctY(p.y_percent)}`).join(" ");
  return (
    <polygon
      points={pts}
      fill={el.fill || "none"}
      stroke={el.stroke || "#1A1A1A"}
      strokeWidth={el.stroke_width ?? 3}
      strokeLinejoin="round"
    />
  );
};

const TimelineBarElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const fillPct = Math.min(100, Math.max(0, el.fill_percent ?? 50));
  const barY = pctY(40);
  const barH = 16;
  const margin = 100;

  return (
    <>
      <rect x={margin} y={barY} width={W - 2 * margin} height={barH} fill={el.remaining_color || "#E0E0E0"} rx={8} />
      <rect x={margin} y={barY} width={((W - 2 * margin) * fillPct) / 100} height={barH} fill={el.fill_color || "#8B4513"} rx={8} />
      <circle cx={margin + ((W - 2 * margin) * fillPct) / 100} cy={barY + barH / 2} r={10} fill={el.fill_color || "#8B4513"} stroke="#1A1A1A" strokeWidth={2} />
      {el.year_label && (
        <text
          x={margin + ((W - 2 * margin) * fillPct) / 100}
          y={barY + 50}
          textAnchor="middle"
          fontSize={32}
          fill="#1A1A1A"
          fontFamily="'Patrick Hand', cursive, sans-serif"
        >
          {el.year_label}
        </text>
      )}
    </>
  );
};

const GroundElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const gy = pctY(el.y_percent ?? 75);
  return (
    <>
      <rect x={0} y={gy} width={W} height={H - gy} fill={el.ground_color || "#8B6914"} />
      <path d={wobbleLine(0, gy, W, gy)} stroke="#1A1A1A" strokeWidth={3} fill="none" opacity={0.3} />
    </>
  );
};

export const ZennBackground: React.FC<ZennBackgroundProps> = ({ bg_color, elements }) => {
  // Render ground first, then everything else in order
  const groundEls = elements.filter((e) => e.type === "ground");
  const otherEls = elements.filter((e) => e.type !== "ground");

  const renderElement = (el: BackgroundElement, i: number) => {
    switch (el.type) {
      case "rect": return <RectElement key={i} el={el} />;
      case "circle": return <CircleElement key={i} el={el} />;
      case "text": return <TextElement key={i} el={el} />;
      case "line": return <LineElement key={i} el={el} />;
      case "path": return <PathElement key={i} el={el} />;
      case "polygon": return <PolygonElement key={i} el={el} />;
      case "timeline_bar": return <TimelineBarElement key={i} el={el} />;
      case "ground": return null; // rendered separately
      default: return null;
    }
  };

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid slice"
      style={{ position: "absolute", inset: 0 }}
    >
      <rect x={0} y={0} width={W} height={H} fill={bg_color || "#FFFFFF"} />
      {groundEls.map((el, i) => <GroundElement key={i} el={el} />)}
      {otherEls.map((el, i) => renderElement(el, i))}
    </svg>
  );
};
