import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SNAPPY } from "../lib/easing";

interface NotificationProps {
  text: string;
  color?: string;
  icon?: string;
  delay?: number;
  y?: number;
}

export const Notification: React.FC<NotificationProps> = ({
  text,
  color = COLORS.cyan,
  icon = "\u2192",
  delay = 0,
  y = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - delay,
    fps,
    config: SPRING_SNAPPY,
  });

  const translateX = 600 * (1 - progress);
  const scale = 0.8 + 0.2 * progress;

  return (
    <div
      style={{
        position: "absolute",
        right: 80,
        top: 200 + y,
        transform: `translateX(${translateX}px) scale(${scale})`,
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "14px 24px",
        borderRadius: 12,
        backgroundColor: `${COLORS.surface}ee`,
        border: `1px solid ${color}44`,
        boxShadow: `0 0 20px ${color}33`,
      }}
    >
      <span style={{ fontSize: 20, color }}>{icon}</span>
      <span
        style={{
          fontSize: 17,
          color: COLORS.text,
          fontFamily: "system-ui, sans-serif",
          fontWeight: 500,
        }}
      >
        {text}
      </span>
    </div>
  );
};
