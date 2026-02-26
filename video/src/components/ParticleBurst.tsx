import React from "react";
import { useCurrentFrame, AbsoluteFill, interpolate } from "remotion";

interface ParticleBurstProps {
  triggerFrame?: number;
  count?: number;
  color?: string;
  radius?: number;
  duration?: number;
  cx?: number;
  cy?: number;
}

// Deterministic pseudo-random using index as seed
const seededRandom = (seed: number): number => {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
};

export const ParticleBurst: React.FC<ParticleBurstProps> = ({
  triggerFrame = 0,
  count = 40,
  color = "#06B6D4",
  radius = 400,
  duration = 30,
  cx = 960,
  cy = 540,
}) => {
  const frame = useCurrentFrame();

  if (frame < triggerFrame || frame > triggerFrame + duration) {
    return null;
  }

  const elapsed = frame - triggerFrame;

  const particles = Array.from({ length: count }, (_, i) => {
    const angle = seededRandom(i * 3 + 1) * Math.PI * 2;
    const speed = 0.5 + seededRandom(i * 3 + 2) * 0.5;
    const size = 3 + seededRandom(i * 3 + 3) * 5;

    const dist = (elapsed / duration) * radius * speed;
    const px = cx + Math.cos(angle) * dist;
    const py = cy + Math.sin(angle) * dist;

    const opacity = interpolate(
      elapsed,
      [0, duration * 0.2, duration],
      [0, 1, 0],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      },
    );

    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: px - size / 2,
          top: py - size / 2,
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: color,
          boxShadow: `0 0 ${size * 2}px ${color}`,
          opacity,
        }}
      />
    );
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>{particles}</AbsoluteFill>
  );
};
