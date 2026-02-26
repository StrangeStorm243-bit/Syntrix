import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_GENTLE } from "../lib/easing";

type Direction = "left" | "right" | "top" | "bottom";

interface TweetBubbleProps {
  handle: string;
  text: string;
  delay?: number;
  from?: Direction;
  x?: number;
  y?: number;
  glowColor?: string;
}

export const TweetBubble: React.FC<TweetBubbleProps> = ({
  handle,
  text,
  delay = 0,
  from = "left",
  x = 0,
  y = 0,
  glowColor = COLORS.twitterBlue,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - delay,
    fps,
    config: SPRING_GENTLE,
  });

  const offscreenH = 1200;
  const offscreenV = 800;

  // Lerp from offscreen origin to target (x, y)
  const origins: Record<Direction, { ox: number; oy: number }> = {
    left: { ox: -offscreenH, oy: 0 },
    right: { ox: offscreenH, oy: 0 },
    top: { ox: 0, oy: -offscreenV },
    bottom: { ox: 0, oy: offscreenV },
  };
  const { ox, oy } = origins[from];
  const tx = ox * (1 - progress) + x * progress;
  const ty = oy * (1 - progress) + y * progress;

  const rotation = (1 - progress) * (from === "right" ? -8 : 8);

  // Avatar gradient based on handle hash
  const hashCode = handle
    .split("")
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  const hue1 = hashCode % 360;
  const hue2 = (hashCode * 7) % 360;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        transform: `translate(-50%, -50%) translate(${tx}px, ${ty}px) rotate(${rotation}deg)`,
        width: 420,
        padding: 24,
        borderRadius: 16,
        backgroundColor: COLORS.surface,
        border: `1px solid ${glowColor}44`,
        boxShadow: `0 0 30px ${glowColor}33, 0 4px 20px rgba(0,0,0,0.4)`,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            background: `linear-gradient(135deg, hsl(${hue1},70%,50%), hsl(${hue2},70%,50%))`,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            color: COLORS.textMuted,
            fontSize: 15,
            fontFamily: "system-ui, sans-serif",
            fontWeight: 600,
          }}
        >
          {handle}
        </span>
      </div>
      <div
        style={{
          color: COLORS.text,
          fontSize: 17,
          fontFamily: "system-ui, sans-serif",
          lineHeight: 1.5,
        }}
      >
        {text}
      </div>
    </div>
  );
};
