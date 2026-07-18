import React from "react";

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

function wobbleOffset(seed: number, amplitude = 2): number {
  return (seededRandom(seed) - 0.5) * 2 * amplitude;
}

function wobblePath(x: number, y: number, w: number, h: number, wobble = 3): string {
  const s = Math.round(x + y * 1000 + w * 2000 + h * 3000);
  const o = (i: number) => wobbleOffset(s + i, wobble);
  const x1 = x + o(1), y1 = y + o(2);
  const x2 = x + w + o(3), y2 = y + o(4);
  const x3 = x + w + o(5), y3 = y + h + o(6);
  const x4 = x + o(7), y4 = y + h + o(8);
  const cp = (i: number) => wobbleOffset(s + 100 + i, wobble * 2);
  return (
    `M ${x1} ${y1} ` +
    `C ${x1 + w / 3 + cp(1)} ${y1 + cp(2)} ${x1 + (2 * w) / 3 + cp(3)} ${y2 + cp(4)} ${x2} ${y2} ` +
    `C ${x2 + cp(5)} ${y2 + h / 3 + cp(6)} ${x3 + cp(7)} ${y3 - h / 3 + cp(8)} ${x3} ${y3} ` +
    `C ${x3 - w / 3 + cp(9)} ${y3 + cp(10)} ${x4 + (2 * w) / 3 + cp(11)} ${y4 + cp(12)} ${x4} ${y4} ` +
    `C ${x4 + cp(13)} ${y4 - h / 3 + cp(14)} ${x1 + cp(15)} ${y1 + h / 3 + cp(16)} ${x1} ${y1}`
  );
}

function wobbleLine(x1: number, y1: number, x2: number, y2: number, wobble = 3): string {
  const s = Math.round(x1 + y1 * 1000 + x2 * 2000 + y2 * 3000);
  const cx1 = x1 + (x2 - x1) / 3;
  const cx2 = x1 + (2 * (x2 - x1)) / 3;
  const wy1 = y1 + wobbleOffset(s + 1, wobble);
  const wy2 = y2 + wobbleOffset(s + 2, wobble);
  return `M ${x1} ${y1} C ${cx1} ${wy1} ${cx2} ${wy2} ${x2} ${y2}`;
}

const W = 1920, H = 1080;
const pctX = (p: number) => (p / 100) * W;
const pctY = (p: number) => (p / 100) * H;
const pctW = (p: number) => (p / 100) * W;
const pctH = (p: number) => (p / 100) * H;

export interface BackgroundElement {
  type: "rect" | "circle" | "text" | "line" | "path" | "polygon" | "timeline_bar" | "ground" | "curve" | "decoration" | "dotted" | "grid";
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
  opacity?: number;
  dasharray?: string;
  rows?: number;
  cols?: number;
  dot_r?: number;
  spacing_x?: number;
  spacing_y?: number;
  from_x?: number;
  from_y?: number;
  to_x?: number;
  to_y?: number;
  control_x?: number;
  control_y?: number;
  shape?: "star" | "cross" | "zigzag";
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
        strokeDasharray={el.dasharray}
        opacity={el.opacity ?? 1}
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
      strokeDasharray={el.dasharray}
      opacity={el.opacity ?? 1}
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
    strokeDasharray={el.dasharray}
    opacity={el.opacity ?? 1}
  />
);

const TextElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const x = pctX(el.x_percent ?? 0);
  const y = pctY(el.y_percent ?? 0);
  const fontSize = el.font_size ?? 48;
  const anchor = el.text_anchor || "start";
  const font = el.font_family || "'Patrick Hand', cursive, sans-serif";

  return (
    <>
      {el.bg_fill && (
        <rect
          x={x - fontSize * 0.15}
          y={y - fontSize * 0.85}
          width={fontSize * (el.content?.length ?? 1) * 0.65 + fontSize * 0.3}
          height={fontSize * 1.3}
          rx={fontSize * 0.12}
          fill={el.bg_fill}
          stroke="#1A1A1A"
          strokeWidth={2}
          opacity={el.opacity ?? 1}
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
        opacity={el.opacity ?? 1}
      >
        {el.content}
      </text>
      {/* underline decoration for title text */}
      {el.fontWeight === "bold" && el.content && el.content.length > 5 && (
        <path
          d={wobbleLine(x - fontSize * 0.1, y + fontSize * 0.4, x + fontSize * (el.content.length) * 0.3, y + fontSize * 0.4)}
          stroke={el.fill || "#1A1A1A"}
          strokeWidth={2}
          fill="none"
          opacity={0.4}
        />
      )}
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
        strokeDasharray={el.dasharray}
        opacity={el.opacity ?? 1}
      />
    );
  }
  return (
    <line
      x1={x1} y1={y1} x2={x2} y2={y2}
      stroke={el.stroke || "#1A1A1A"}
      strokeWidth={strokeW}
      strokeLinecap="round"
      strokeDasharray={el.dasharray}
      opacity={el.opacity ?? 1}
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
      strokeDasharray={el.dasharray}
      opacity={el.opacity ?? 1}
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
      strokeDasharray={el.dasharray}
      opacity={el.opacity ?? 1}
    />
  );
};

const CurveElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const fx = pctX(el.from_x ?? 0);
  const fy = pctY(el.from_y ?? 50);
  const tx = pctX(el.to_x ?? 100);
  const ty = pctY(el.to_y ?? 50);
  const cx = pctX(el.control_x ?? 50);
  const cy = pctY(el.control_y ?? 20);
  return (
    <path
      d={`M ${fx} ${fy} Q ${cx} ${cy} ${tx} ${ty}`}
      stroke={el.stroke || "#1A1A1A"}
      strokeWidth={el.stroke_width ?? 2}
      fill="none"
      strokeLinecap="round"
      strokeDasharray={el.dasharray}
      opacity={el.opacity ?? 0.5}
    />
  );
};

const DottedElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const dots: React.ReactNode[] = [];
  const rows = el.rows ?? 5;
  const cols = el.cols ?? 8;
  const r = pctW(el.dot_r ?? 0.3);
  const spacingX = pctW(el.spacing_x ?? 12);
  const spacingY = pctH(el.spacing_y ?? 10);
  const startX = pctX(el.x_percent ?? 5);
  const startY = pctY(el.y_percent ?? 10);
  const dotColor = el.fill || "#1A1A1A";

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const ox = seededRandom(row * 1000 + col) * 3;
      const oy = seededRandom(row * 1000 + col + 500) * 3;
      dots.push(
        <circle
          key={`${row}-${col}`}
          cx={startX + col * spacingX + ox}
          cy={startY + row * spacingY + oy}
          r={r}
          fill={dotColor}
          opacity={el.opacity ?? 0.15}
        />
      );
    }
  }
  return <>{dots}</>;
};

const GridElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const lines: React.ReactNode[] = [];
  const rows = el.rows ?? 5;
  const cols = el.cols ?? 8;
  const spacingX = pctW(el.spacing_x ?? 12);
  const spacingY = pctH(el.spacing_y ?? 10);
  const startX = pctX(el.x_percent ?? 0);
  const startY = pctY(el.y_percent ?? 0);
  const w = cols * spacingX;
  const h = rows * spacingY;
  const strokeColor = el.stroke || "#1A1A1A";
  const sw = el.stroke_width ?? 1;

  for (let r = 0; r <= rows; r++) {
    const y = startY + r * spacingY;
    const s = Math.round(startX + y * 100);
    lines.push(
      <line key={`hr-${r}`}
        x1={startX + wobbleOffset(s, 2)}
        y1={y + wobbleOffset(s + 1, 2)}
        x2={startX + w + wobbleOffset(s + 2, 2)}
        y2={y + wobbleOffset(s + 3, 2)}
        stroke={strokeColor} strokeWidth={sw} opacity={el.opacity ?? 0.1}
      />
    );
  }
  for (let c = 0; c <= cols; c++) {
    const x = startX + c * spacingX;
    const s = Math.round(x + startY * 100);
    lines.push(
      <line key={`vc-${c}`}
        x1={x + wobbleOffset(s, 2)}
        y1={startY + wobbleOffset(s + 1, 2)}
        x2={x + wobbleOffset(s + 2, 2)}
        y2={startY + h + wobbleOffset(s + 3, 2)}
        stroke={strokeColor} strokeWidth={sw} opacity={el.opacity ?? 0.1}
      />
    );
  }
  return <>{lines}</>;
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
      {/* wobble dot */}
      <circle cx={margin + ((W - 2 * margin) * fillPct) / 100 + wobbleOffset(fillPct, 3)} cy={barY + barH / 2 + wobbleOffset(fillPct + 1, 3)} r={10} fill={el.fill_color || "#8B4513"} stroke="#1A1A1A" strokeWidth={2} />
      {el.year_label && (
        <text
          x={margin + ((W - 2 * margin) * fillPct) / 100}
          y={barY + 55}
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
  const color = el.ground_color || "#8B6914";
  return (
    <>
      <rect x={0} y={gy} width={W} height={H - gy} fill={color} />
      <path d={wobbleLine(0, gy, W, gy)} stroke="#1A1A1A" strokeWidth={4} fill="none" opacity={0.4} />
      {/* texture lines on ground */}
      <path d={wobbleLine(50, gy + 20, 200, gy + 25)} stroke="#1A1A1A" strokeWidth={1} fill="none" opacity={0.1} />
      <path d={wobbleLine(300, gy + 40, 500, gy + 35)} stroke="#1A1A1A" strokeWidth={1} fill="none" opacity={0.1} />
      <path d={wobbleLine(600, gy + 15, 800, gy + 20)} stroke="#1A1A1A" strokeWidth={1} fill="none" opacity={0.1} />
    </>
  );
};

const DecorationElement: React.FC<{ el: BackgroundElement }> = ({ el }) => {
  const cx = pctX(el.cx_percent ?? 50);
  const cy = pctY(el.cy_percent ?? 50);
  const r = pctW(el.r_percent ?? 2);
  const shape = el.shape || "star";

  if (shape === "star") {
    const pts = [];
    for (let i = 0; i < 5; i++) {
      const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
      const outerR = r;
      pts.push(`${cx + Math.cos(angle) * outerR},${cy + Math.sin(angle) * outerR}`);
      const innerAngle = angle + Math.PI / 5;
      const innerR = r * 0.4;
      pts.push(`${cx + Math.cos(innerAngle) * innerR},${cy + Math.sin(innerAngle) * innerR}`);
    }
    return (
      <polygon
        points={pts.join(" ")}
        fill={el.fill || "#1A1A1A"}
        opacity={el.opacity ?? 0.2}
      />
    );
  }

  if (shape === "cross") {
    return (
      <>
        <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} stroke={el.fill || "#1A1A1A"} strokeWidth={2} opacity={el.opacity ?? 0.2} />
        <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} stroke={el.fill || "#1A1A1A"} strokeWidth={2} opacity={el.opacity ?? 0.2} />
      </>
    );
  }

  // zigzag
  const pts = [];
  for (let i = 0; i <= 10; i++) {
    const t = i / 10;
    const x = cx - r * 3 + t * r * 6;
    const y = cy + (i % 2 === 0 ? -r * 0.5 : r * 0.5);
    pts.push(`${x},${y}`);
  }
  return (
    <polyline
      points={pts.join(" ")}
      stroke={el.fill || "#1A1A1A"}
      strokeWidth={1.5}
      fill="none"
      opacity={el.opacity ?? 0.15}
    />
  );
};

export const ZennBackground: React.FC<ZennBackgroundProps> = ({ bg_color, elements }) => {
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
      case "ground": return null;
      case "curve": return <CurveElement key={i} el={el} />;
      case "decoration": return <DecorationElement key={i} el={el} />;
      case "dotted": return <DottedElement key={i} el={el} />;
      case "grid": return <GridElement key={i} el={el} />;
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
      {/* Paper texture overlay */}
      <rect x={0} y={0} width={W} height={H} fill={bg_color || "#FFFFFF"} />
      {groundEls.map((el, i) => <GroundElement key={i} el={el} />)}
      {otherEls.map((el, i) => renderElement(el, i))}
    </svg>
  );
};
