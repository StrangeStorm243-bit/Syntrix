import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { PipelineStage } from "../components/PipelineStage";
import { Scanlines } from "../components/Scanlines";

const STAGES = [
  { label: "Collect", icon: "\uD83D\uDD0D", color: COLORS.cyan },
  { label: "Normalize", icon: "\uD83D\uDCC4", color: COLORS.cyan },
  { label: "Judge", icon: "\u2696\uFE0F", color: COLORS.blue },
  { label: "Score", icon: "\uD83D\uDCCA", color: COLORS.blue },
  { label: "Draft", icon: "\u270F\uFE0F", color: COLORS.magenta },
  { label: "Approve", icon: "\u2705", color: COLORS.green },
  { label: "Send", icon: "\uD83D\uDE80", color: COLORS.magenta },
  { label: "DM", icon: "\uD83D\uDCAC", color: COLORS.magenta },
];

const STAGE_SPACING = 1600 / (STAGES.length - 1);
const STAGE_START_X = (1920 - 1600) / 2; // center 1600px across 1920
const STAGE_Y = 420;

export const ThePipeline: React.FC = () => {
  const frame = useCurrentFrame();

  // Section heading fade in
  const headingOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Callout appears after stage 5 (Approve) activates: stage 5 activateAt = 5 * 45 + 20 = 245
  const calloutOpacity = interpolate(frame, [260, 290], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Subtle grid pattern */}
      <AbsoluteFill
        style={{
          backgroundImage: `
            linear-gradient(${COLORS.textMuted}08 1px, transparent 1px),
            linear-gradient(90deg, ${COLORS.textMuted}08 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />

      {/* Section heading */}
      <div
        style={{
          position: "absolute",
          top: 120,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: headingOpacity,
        }}
      >
        <div
          style={{
            fontSize: 44,
            fontWeight: 700,
            fontFamily: "system-ui, sans-serif",
            color: COLORS.text,
          }}
        >
          From signal to sent —{" "}
          <span style={{ color: COLORS.cyan }}>in one pipeline</span>
        </div>
        <div
          style={{
            fontSize: 20,
            fontFamily: "system-ui, sans-serif",
            color: COLORS.textMuted,
            marginTop: 12,
          }}
        >
          8 stages, fully automated, always under your control
        </div>
      </div>

      {/* Connecting lines between stages */}
      <svg
        width={1920}
        height={1080}
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {STAGES.slice(0, -1).map((_, i) => {
          const fromX = STAGE_START_X + i * STAGE_SPACING + 32;
          const toX = STAGE_START_X + (i + 1) * STAGE_SPACING + 32;
          const lineY = STAGE_Y + 32;
          const activateAt = i * 45 + 20;

          // Animate line x2 from fromX to toX
          const lineProgress = interpolate(
            frame,
            [activateAt + 20, activateAt + 55],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            },
          );
          const currentX2 = fromX + (toX - fromX) * lineProgress;

          return (
            <line
              key={i}
              x1={fromX}
              y1={lineY}
              x2={currentX2}
              y2={lineY}
              stroke={STAGES[i].color}
              strokeWidth={2}
              opacity={0.5}
              strokeDasharray="8 4"
            />
          );
        })}
      </svg>

      {/* Pipeline stages */}
      {STAGES.map((stage, i) => (
        <PipelineStage
          key={stage.label}
          label={stage.label}
          icon={stage.icon}
          color={stage.color}
          activateAt={i * 45 + 20}
          x={STAGE_START_X + i * STAGE_SPACING}
          y={STAGE_Y}
        />
      ))}

      {/* Human approval callout */}
      <div
        style={{
          position: "absolute",
          bottom: 140,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: calloutOpacity,
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "16px 40px",
            borderRadius: 12,
            backgroundColor: `${COLORS.green}18`,
            border: `1px solid ${COLORS.green}44`,
          }}
        >
          <span
            style={{
              fontSize: 24,
              fontWeight: 600,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.green,
            }}
          >
            Human approves every draft — zero spam, full control
          </span>
        </div>
      </div>

      {/* Scanlines overlay */}
      <Scanlines opacity={0.03} />
    </AbsoluteFill>
  );
};
