import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { SPRING_SNAPPY } from "../lib/easing";

interface PipelineStageProps {
  label: string;
  icon: string;
  color: string;
  activateAt?: number;
  x: number;
  y: number;
}

export const PipelineStage: React.FC<PipelineStageProps> = ({
  label,
  icon,
  color,
  activateAt = 0,
  x,
  y,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - activateAt,
    fps,
    config: SPRING_SNAPPY,
  });

  const scale = progress;
  const glowIntensity = Math.round(progress * 40);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          backgroundColor: `${color}22`,
          border: `2px solid ${color}`,
          boxShadow: `0 0 ${glowIntensity}px ${color}66`,
        }}
      >
        {icon}
      </div>
      <span
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: color,
          fontFamily: "system-ui, sans-serif",
          textAlign: "center",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>
    </div>
  );
};
