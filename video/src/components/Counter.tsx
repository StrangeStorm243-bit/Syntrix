import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

interface CounterProps {
  from?: number;
  to: number;
  startAt?: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  fontSize?: number;
  color?: string;
  formatFn?: (n: number) => string;
}

const defaultFormat = (n: number): string => {
  if (n >= 1_000_000) {
    return `${(n / 1_000_000).toFixed(1)}M`;
  }
  if (n >= 1_000) {
    const k = n / 1_000;
    return k >= 10 ? `${Math.round(k)}K` : `${k.toFixed(1)}K`;
  }
  return Math.round(n).toLocaleString();
};

export const Counter: React.FC<CounterProps> = ({
  from = 0,
  to,
  startAt = 0,
  duration = 60,
  prefix = "",
  suffix = "",
  fontSize = 64,
  color = "#FFFFFF",
  formatFn = defaultFormat,
}) => {
  const frame = useCurrentFrame();

  const value = interpolate(frame, [startAt, startAt + duration], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        fontSize,
        color,
        fontFamily: "monospace",
        fontWeight: 700,
        textAlign: "center",
      }}
    >
      {prefix}
      {formatFn(value)}
      {suffix}
    </div>
  );
};
