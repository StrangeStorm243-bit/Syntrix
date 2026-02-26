import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SNAPPY } from "../lib/easing";

export const CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo springs in with scale 0.5 -> 1
  const logoScale = spring({
    frame,
    fps,
    config: SPRING_SNAPPY,
    from: 0.5,
    to: 1,
  });

  // Three CTA lines fade in staggered
  const line1Opacity = interpolate(frame, [8, 13], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const line2Opacity = interpolate(frame, [13, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const line3Opacity = interpolate(frame, [18, 23], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.base,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 32,
      }}
    >
      {/* Syntrix logo */}
      <div style={{ transform: `scale(${logoScale})` }}>
        <span
          style={{
            fontSize: 72,
            fontWeight: 800,
            fontFamily: "system-ui, sans-serif",
            background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.magenta})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Syntrix
        </span>
      </div>

      {/* CTA lines */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          marginTop: 16,
        }}
      >
        {/* Docker command */}
        <div style={{ opacity: line1Opacity }}>
          <span
            style={{
              fontSize: 26,
              fontFamily: "monospace",
              fontWeight: 600,
              color: COLORS.green,
              backgroundColor: `${COLORS.green}18`,
              padding: "10px 28px",
              borderRadius: 10,
            }}
          >
            docker compose up
          </span>
        </div>

        {/* Website */}
        <div style={{ opacity: line2Opacity }}>
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.cyan,
            }}
          >
            syntrix.app
          </span>
        </div>

        {/* GitHub */}
        <div style={{ opacity: line3Opacity }}>
          <span
            style={{
              fontSize: 22,
              fontWeight: 500,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.textMuted,
            }}
          >
            {"\u2B50"} Star on GitHub
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
