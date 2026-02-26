import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../lib/colors";

interface HockeyStickProps {
  startFrame?: number;
  duration?: number;
}

export const HockeyStick: React.FC<HockeyStickProps> = ({
  startFrame = 0,
  duration = 180,
}) => {
  const frame = useCurrentFrame();

  if (frame < startFrame) {
    return null;
  }

  const rawProgress = (frame - startFrame) / duration;
  const progress = Math.max(0, Math.min(1, rawProgress));

  // Chart area
  const chartX = 200;
  const chartWidth = 800;
  const chartY = 200;
  const chartHeight = 600;
  const chartBottom = chartY + chartHeight;

  // Generate exponential curve points
  const totalPoints = 50;
  const pointCount = Math.max(2, Math.round(progress * totalPoints));

  const points: Array<{ x: number; y: number }> = [];
  for (let i = 0; i < pointCount; i++) {
    const t = i / (totalPoints - 1);
    const value = Math.pow(t, 3.5);
    const px = chartX + t * chartWidth;
    const py = chartBottom - value * chartHeight;
    points.push({ x: px, y: py });
  }

  // Build SVG path
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  // Filled area path (closes to bottom)
  const areaPath =
    linePath +
    ` L ${points[points.length - 1].x} ${chartBottom}` +
    ` L ${points[0].x} ${chartBottom} Z`;

  // Tip position
  const tip = points[points.length - 1];
  const tipPulse = interpolate(
    Math.sin(frame * 0.2),
    [-1, 1],
    [6, 10],
  );

  // Grid lines at 25%, 50%, 75%, 100%
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  return (
    <svg
      width={1920}
      height={1080}
      viewBox="0 0 1920 1080"
      style={{ position: "absolute", top: 0, left: 0 }}
    >
      {/* Grid lines */}
      {gridLevels.map((level) => {
        const gy = chartBottom - level * chartHeight;
        return (
          <line
            key={level}
            x1={chartX}
            y1={gy}
            x2={chartX + chartWidth}
            y2={gy}
            stroke={COLORS.textMuted}
            strokeWidth={1}
            strokeDasharray="6 4"
            opacity={0.3}
          />
        );
      })}

      {/* Baseline */}
      <line
        x1={chartX}
        y1={chartBottom}
        x2={chartX + chartWidth}
        y2={chartBottom}
        stroke={COLORS.textMuted}
        strokeWidth={1}
        opacity={0.5}
      />

      {/* Y-axis */}
      <line
        x1={chartX}
        y1={chartY}
        x2={chartX}
        y2={chartBottom}
        stroke={COLORS.textMuted}
        strokeWidth={1}
        opacity={0.5}
      />

      {/* Filled area under curve */}
      <path
        d={areaPath}
        fill={COLORS.moneyGreen}
        opacity={22 / 255}
      />

      {/* Glow line */}
      <path
        d={linePath}
        fill="none"
        stroke={COLORS.moneyGreen}
        strokeWidth={12}
        opacity={0.3}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Main stroke line */}
      <path
        d={linePath}
        fill="none"
        stroke={COLORS.moneyGreen}
        strokeWidth={4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Pulsing tip dot */}
      <circle
        cx={tip.x}
        cy={tip.y}
        r={tipPulse}
        fill={COLORS.moneyGreen}
        opacity={0.9}
      />
      <circle
        cx={tip.x}
        cy={tip.y}
        r={tipPulse * 2}
        fill="none"
        stroke={COLORS.moneyGreen}
        strokeWidth={2}
        opacity={0.3}
      />

      {/* Y-axis labels */}
      <text
        x={chartX - 20}
        y={chartBottom + 5}
        textAnchor="end"
        fill={COLORS.textMuted}
        fontSize={16}
        fontFamily="monospace"
      >
        $0
      </text>
      <text
        x={chartX - 20}
        y={chartY + 5}
        textAnchor="end"
        fill={COLORS.textMuted}
        fontSize={16}
        fontFamily="monospace"
      >
        $1M
      </text>

      {/* X-axis label */}
      <text
        x={chartX + chartWidth / 2}
        y={chartBottom + 50}
        textAnchor="middle"
        fill={COLORS.textMuted}
        fontSize={18}
        fontFamily="system-ui, sans-serif"
        fontWeight={500}
      >
        Monthly Recurring Revenue
      </text>
    </svg>
  );
};
