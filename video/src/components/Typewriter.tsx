import React from "react";
import { useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";

interface TypewriterProps {
  text: string;
  speed?: number;
  delay?: number;
  fontSize?: number;
  color?: string;
  fontFamily?: string;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  speed = 2,
  delay = 0,
  fontSize = 32,
  color = COLORS.text,
  fontFamily = "monospace",
}) => {
  const frame = useCurrentFrame();

  const elapsed = Math.max(0, frame - delay);
  const charsToShow = Math.min(text.length, Math.floor(elapsed / speed));
  const isTyping = charsToShow < text.length;

  // Cursor blinks using sine wave
  const cursorOpacity = isTyping
    ? 1
    : Math.sin(frame * 0.3) > 0
      ? 1
      : 0;

  return (
    <div
      style={{
        fontSize,
        color,
        fontFamily,
        whiteSpace: "pre-wrap",
        lineHeight: 1.5,
      }}
    >
      {text.slice(0, charsToShow)}
      <span
        style={{
          color: COLORS.cyan,
          opacity: cursorOpacity,
        }}
      >
        {"\u2588"}
      </span>
    </div>
  );
};
