import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { Notification } from "../components/Notification";

const NOTIFICATIONS = [
  { text: "Reply sent to @techleadSara", icon: "\u2192", color: COLORS.cyan, delay: 15 },
  { text: "DM delivered to @devops_mike", icon: "\u2709", color: COLORS.magenta, delay: 50 },
  { text: "@ctojennifer viewed your profile", icon: "\uD83D\uDC41", color: COLORS.text, delay: 80 },
  { text: "New follower: @ctojennifer", icon: "+", color: COLORS.green, delay: 105 },
  { text: "Inbound DM: 'Hey, can we chat about Syntrix?'", icon: "\uD83D\uDCAC", color: COLORS.gold, delay: 130 },
  { text: "Reply sent to @growthguru", icon: "\u2192", color: COLORS.cyan, delay: 155 },
  { text: "DM delivered to @saas_founder", icon: "\u2709", color: COLORS.magenta, delay: 170 },
  { text: "3 new followers this hour", icon: "\uD83D\uDCC8", color: COLORS.green, delay: 185 },
  { text: "Inbound: 'Love what you're building!'", icon: "\uD83D\uDCAC", color: COLORS.gold, delay: 195 },
  { text: "Demo request from @enterprise_cto", icon: "\uD83D\uDD25", color: COLORS.gold, delay: 210 },
  { text: "Pipeline: 12 new high-score leads", icon: "\u26A1", color: COLORS.cyan, delay: 220 },
  { text: "Revenue alert: $2,400 MRR milestone", icon: "\uD83D\uDCB0", color: COLORS.moneyGreen, delay: 240 },
];

export const TheResults: React.FC = () => {
  const frame = useCurrentFrame();

  // Pulsing cyan glow for status circle
  const pulsePhase = Math.sin(frame * 0.08);
  const glowSize = 8 + pulsePhase * 4;
  const glowOpacity = 0.4 + pulsePhase * 0.2;

  // Running indicator blink
  const indicatorOpacity = Math.sin(frame * 0.15) > -0.3 ? 1 : 0.4;

  // Left panel fade in
  const leftOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Left panel: 45% */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "45%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          opacity: leftOpacity,
          padding: 60,
        }}
      >
        {/* Pulsing circle border */}
        <div
          style={{
            width: 220,
            height: 220,
            borderRadius: "50%",
            border: `3px solid ${COLORS.cyan}`,
            boxShadow: `0 0 ${glowSize * 2}px ${COLORS.cyan}${Math.round(glowOpacity * 255)
              .toString(16)
              .padStart(2, "0")}, inset 0 0 ${glowSize}px ${COLORS.cyan}${Math.round(glowOpacity * 128)
              .toString(16)
              .padStart(2, "0")}`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            marginBottom: 40,
          }}
        >
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              fontFamily: "monospace",
              color: COLORS.cyan,
              textTransform: "uppercase",
              letterSpacing: 3,
            }}
          >
            Pipeline
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 800,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.text,
            }}
          >
            ACTIVE
          </div>
        </div>

        {/* Running indicator */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 24,
            opacity: indicatorOpacity,
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              backgroundColor: COLORS.green,
              boxShadow: `0 0 8px ${COLORS.green}`,
            }}
          />
          <span
            style={{
              fontSize: 18,
              fontWeight: 600,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.green,
            }}
          >
            Running
          </span>
        </div>

        {/* Subtext */}
        <div
          style={{
            fontSize: 20,
            fontFamily: "system-ui, sans-serif",
            color: COLORS.textMuted,
            textAlign: "center",
            lineHeight: 1.5,
          }}
        >
          Syntrix is working while you sleep.
        </div>
      </div>

      {/* Divider */}
      <div
        style={{
          position: "absolute",
          left: "45%",
          top: 80,
          bottom: 80,
          width: 1,
          backgroundColor: `${COLORS.textMuted}33`,
        }}
      />

      {/* Right panel: 55% — notifications */}
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: "55%",
        }}
      >
        {/* Heading */}
        <div
          style={{
            position: "absolute",
            top: 80,
            left: 60,
            fontSize: 28,
            fontWeight: 700,
            fontFamily: "system-ui, sans-serif",
            color: COLORS.text,
          }}
        >
          Live Activity
        </div>

        {/* Notification stack */}
        {NOTIFICATIONS.map((notif, i) => (
          <Notification
            key={i}
            text={notif.text}
            icon={notif.icon}
            color={notif.color}
            delay={notif.delay}
            y={i * 62}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
