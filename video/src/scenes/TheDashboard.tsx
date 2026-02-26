import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_GENTLE } from "../lib/easing";
import { Counter } from "../components/Counter";

const METRICS = [
  { label: "Collected", value: 1247, color: COLORS.cyan },
  { label: "Relevant", value: 389, color: COLORS.blue },
  { label: "Drafted", value: 87, color: COLORS.magenta },
  { label: "Sent", value: 58, color: COLORS.green },
];

const NAV_ITEMS = [
  { label: "Dashboard", active: true },
  { label: "Leads", active: false },
  { label: "Queue", active: false },
  { label: "Analytics", active: false },
  { label: "Settings", active: false },
];

const QUEUE_ROWS = [
  {
    id: "#1042",
    handle: "@techleadSara",
    draft: "Hey Sara, noticed your thread on CI bottlenecks...",
    score: "94",
  },
  {
    id: "#1043",
    handle: "@devops_mike",
    draft: "Mike, your take on deploy frequency is spot on...",
    score: "88",
  },
  {
    id: "#1044",
    handle: "@growthguru",
    draft: "Love your growth framework thread! Syntrix automates...",
    score: "82",
  },
];

export const TheDashboard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Dashboard container slides up from bottom
  const slideUp = spring({
    frame,
    fps,
    config: SPRING_GENTLE,
  });
  const containerY = interpolate(slideUp, [0, 1], [800, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      <div
        style={{
          position: "absolute",
          top: 40 + containerY,
          left: 80,
          right: 80,
          bottom: 40,
          borderRadius: 20,
          backgroundColor: COLORS.surface,
          border: `1px solid ${COLORS.cyan}44`,
          boxShadow: `0 0 60px ${COLORS.cyan}22`,
          display: "flex",
          overflow: "hidden",
        }}
      >
        {/* Left sidebar */}
        <div
          style={{
            width: 220,
            borderRight: `1px solid ${COLORS.cyan}22`,
            padding: "30px 0",
            display: "flex",
            flexDirection: "column",
            gap: 4,
          }}
        >
          {/* Logo + version */}
          <div
            style={{
              padding: "0 24px 24px",
              borderBottom: `1px solid ${COLORS.cyan}22`,
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span
              style={{
                fontSize: 22,
                fontWeight: 700,
                fontFamily: "system-ui, sans-serif",
                color: COLORS.text,
              }}
            >
              Syntrix
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: COLORS.magenta,
                backgroundColor: `${COLORS.magenta}22`,
                padding: "2px 8px",
                borderRadius: 6,
              }}
            >
              v0.3
            </span>
          </div>

          {/* Nav items */}
          {NAV_ITEMS.map((item) => (
            <div
              key={item.label}
              style={{
                padding: "10px 24px",
                fontSize: 15,
                fontWeight: item.active ? 600 : 400,
                fontFamily: "system-ui, sans-serif",
                color: item.active ? COLORS.cyan : COLORS.textMuted,
                backgroundColor: item.active ? `${COLORS.cyan}11` : "transparent",
                borderLeft: item.active ? `3px solid ${COLORS.cyan}` : "3px solid transparent",
              }}
            >
              {item.label}
            </div>
          ))}
        </div>

        {/* Main content area */}
        <div style={{ flex: 1, padding: 32, overflow: "hidden" }}>
          {/* Metric cards */}
          <div style={{ display: "flex", gap: 20, marginBottom: 32 }}>
            {METRICS.map((metric, i) => {
              const cardOpacity = interpolate(
                frame,
                [10 + i * 8, 18 + i * 8],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              );
              const cardY = interpolate(
                frame,
                [10 + i * 8, 18 + i * 8],
                [20, 0],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              );

              return (
                <div
                  key={metric.label}
                  style={{
                    flex: 1,
                    padding: "20px 24px",
                    borderRadius: 12,
                    backgroundColor: `${metric.color}11`,
                    border: `1px solid ${metric.color}33`,
                    opacity: cardOpacity,
                    transform: `translateY(${cardY}px)`,
                  }}
                >
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      fontFamily: "system-ui, sans-serif",
                      color: metric.color,
                      marginBottom: 8,
                      textTransform: "uppercase",
                      letterSpacing: 1,
                    }}
                  >
                    {metric.label}
                  </div>
                  <Counter
                    to={metric.value}
                    startAt={13 + i * 8}
                    duration={30}
                    fontSize={36}
                    color={COLORS.text}
                    formatFn={(n: number) => Math.round(n).toLocaleString()}
                  />
                </div>
              );
            })}
          </div>

          {/* Draft queue table */}
          <div>
            <div
              style={{
                fontSize: 18,
                fontWeight: 600,
                fontFamily: "system-ui, sans-serif",
                color: COLORS.text,
                marginBottom: 16,
              }}
            >
              Draft Queue
            </div>

            {/* Table header */}
            <div
              style={{
                display: "flex",
                padding: "10px 16px",
                borderBottom: `1px solid ${COLORS.textMuted}33`,
                gap: 16,
              }}
            >
              {["ID", "Handle", "Draft", "Score", "Status"].map((h) => (
                <div
                  key={h}
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: "system-ui, sans-serif",
                    color: COLORS.textMuted,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                    flex: h === "Draft" ? 3 : 1,
                    minWidth: h === "ID" ? 60 : undefined,
                  }}
                >
                  {h}
                </div>
              ))}
            </div>

            {/* Table rows */}
            {QUEUE_ROWS.map((row, i) => {
              const rowAppearFrame = 50 + i * 18;
              const rowOpacity = interpolate(
                frame,
                [rowAppearFrame, rowAppearFrame + 8],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                },
              );

              // Status badge flips to approved 25 frames after row appears
              const approveFrame = rowAppearFrame + 25;
              const isApproved = frame >= approveFrame;
              const badgeColor = isApproved ? COLORS.green : COLORS.gold;
              const badgeText = isApproved ? "\u2713 Approved" : "Pending";

              return (
                <div
                  key={row.id}
                  style={{
                    display: "flex",
                    padding: "12px 16px",
                    borderBottom: `1px solid ${COLORS.textMuted}15`,
                    gap: 16,
                    alignItems: "center",
                    opacity: rowOpacity,
                  }}
                >
                  <div
                    style={{
                      fontSize: 14,
                      fontFamily: "monospace",
                      color: COLORS.textMuted,
                      flex: 1,
                      minWidth: 60,
                    }}
                  >
                    {row.id}
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontFamily: "system-ui, sans-serif",
                      fontWeight: 600,
                      color: COLORS.cyan,
                      flex: 1,
                    }}
                  >
                    {row.handle}
                  </div>
                  <div
                    style={{
                      fontSize: 13,
                      fontFamily: "system-ui, sans-serif",
                      color: COLORS.text,
                      flex: 3,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {row.draft}
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontFamily: "monospace",
                      fontWeight: 700,
                      color: COLORS.text,
                      flex: 1,
                      textAlign: "center",
                    }}
                  >
                    {row.score}
                  </div>
                  <div
                    style={{
                      flex: 1,
                      display: "flex",
                      justifyContent: "center",
                    }}
                  >
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        fontFamily: "system-ui, sans-serif",
                        color: badgeColor,
                        backgroundColor: `${badgeColor}22`,
                        padding: "4px 12px",
                        borderRadius: 8,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {badgeText}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
