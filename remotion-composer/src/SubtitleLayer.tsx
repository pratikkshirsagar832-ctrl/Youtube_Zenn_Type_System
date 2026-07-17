import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

// ---------------------------------------------------------------------------
// SubtitleLayer — word-by-word gold captions
// Shows 4 words at a time (2 before + current + 1 after).
// Current word: large + bold.
// Keyword (is_keyword): gold (#F4D03F).
// Non-keyword current: white.
// Adjacent words: dimmed gray.
// ---------------------------------------------------------------------------

export interface SubtitleWord {
  word: string;
  start: number;
  end: number;
  is_keyword: boolean;
}

export interface SubtitleLayerProps {
  words: SubtitleWord[];
  fps?: number;
}

const KEYWORD_GOLD = "#F4D03F";
const CURRENT_WHITE = "#FFFFFF";
const ADJACENT_GRAY = "#888888";

export const SubtitleLayer: React.FC<SubtitleLayerProps> = ({ words, fps = 30 }) => {
  const frame = useCurrentFrame();
  const currentTime = frame / fps;

  if (!words || words.length === 0) return null;

  const currentWordIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime < w.end,
  );

  if (currentWordIndex < 0) return null;

  const visibleStart = Math.max(0, currentWordIndex - 2);
  const visibleEnd = Math.min(words.length, currentWordIndex + 3);
  const visibleWords = words.slice(visibleStart, visibleEnd);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "baseline",
          gap: 14,
          padding: "16px 60px",
          flexWrap: "wrap",
          fontFamily: "Arial, Helvetica, sans-serif",
          background: "linear-gradient(transparent 0%, rgba(0,0,0,0.5) 100%)",
        }}
      >
        {visibleWords.map((w, i) => {
          const absoluteIndex = visibleStart + i;
          const isCurrent = absoluteIndex === currentWordIndex;
          const color = isCurrent
            ? w.is_keyword
              ? KEYWORD_GOLD
              : CURRENT_WHITE
            : ADJACENT_GRAY;
          const fontSize = isCurrent ? 52 : 38;
          const fontWeight = isCurrent ? 800 : 400;
          return (
            <span
              key={`${absoluteIndex}-${w.word}`}
              style={{
                color,
                fontSize,
                fontWeight,
                textShadow: "0 2px 12px rgba(0,0,0,0.9), 0 0 6px rgba(0,0,0,0.7)",
                lineHeight: 1.2,
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
