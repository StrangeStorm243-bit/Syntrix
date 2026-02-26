import React from "react";
import { useCurrentFrame, AbsoluteFill, interpolate } from "remotion";

interface MoneyRainProps {
  count?: number;
  startFrame?: number;
}

const SYMBOLS = ["$", "\uD83D\uDCB0", "\uD83D\uDCB5", "\uD83E\uDD11", "$", "$", "$", "\uD83D\uDCB8"];

// Deterministic pseudo-random using index as seed
const seededRandom = (seed: number): number => {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
};

export const MoneyRain: React.FC<MoneyRainProps> = ({
  count = 60,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();

  if (frame < startFrame) {
    return null;
  }

  const elapsed = frame - startFrame;

  const particles = Array.from({ length: count }, (_, i) => {
    const xPos = seededRandom(i * 5 + 1) * 1920;
    const fallSpeed = 4 + seededRandom(i * 5 + 2) * 6;
    const staggerDelay = seededRandom(i * 5 + 3) * 40;
    const symbolIndex = Math.floor(seededRandom(i * 5 + 4) * SYMBOLS.length);
    const symbol = SYMBOLS[symbolIndex];
    const size = 20 + seededRandom(i * 5 + 5) * 30;
    const rotation = seededRandom(i * 5 + 6) * 360;

    const particleElapsed = elapsed - staggerDelay;
    if (particleElapsed < 0) return null;

    const yPos = -60 + particleElapsed * fallSpeed;
    if (yPos > 1140) return null;

    const opacity = interpolate(particleElapsed, [0, 10], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: xPos,
          top: yPos,
          fontSize: size,
          transform: `rotate(${rotation}deg)`,
          opacity,
          pointerEvents: "none",
        }}
      >
        {symbol}
      </div>
    );
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", pointerEvents: "none" }}>
      {particles}
    </AbsoluteFill>
  );
};
