import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SLAM } from "../lib/easing";
import { Typewriter } from "../components/Typewriter";
import { ParticleBurst } from "../components/ParticleBurst";

export const EnterSyntrix: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Aurora gradient wipe — radial gradient appears over first 15 frames
  const auroraOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Logo spring-slam: scale 3 -> 1 starting at frame 15
  const logoScale = spring({
    frame: frame - 15,
    fps,
    config: SPRING_SLAM,
    from: 3,
    to: 1,
  });

  const logoOpacity = interpolate(frame, [15, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Subtext fade in at frame 100-120
  const subtextOpacity = interpolate(frame, [100, 120], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Aurora gradient wipe */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${COLORS.cyan}44, ${COLORS.magenta}22, transparent 70%)`,
          opacity: auroraOpacity,
        }}
      />

      {/* Syntrix logo */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: 0,
          right: 0,
          textAlign: "center",
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
        }}
      >
        <span
          style={{
            fontSize: 96,
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

      {/* Particle burst at frame 20 */}
      <ParticleBurst
        triggerFrame={20}
        count={50}
        color={COLORS.cyan}
        radius={500}
        duration={30}
        cx={960}
        cy={540}
      />

      {/* Typewriter: "Find.  Engage.  Convert." */}
      <div
        style={{
          position: "absolute",
          top: "52%",
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Typewriter
          text="Find.  Engage.  Convert."
          speed={3}
          delay={40}
          fontSize={40}
          color={COLORS.text}
          fontFamily="monospace"
        />
      </div>

      {/* Subtext */}
      <div
        style={{
          position: "absolute",
          top: "64%",
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: subtextOpacity,
          fontSize: 22,
          fontFamily: "system-ui, sans-serif",
          color: COLORS.textMuted,
        }}
      >
        Open-source AI outreach — self-hosted, human-approved.
      </div>
    </AbsoluteFill>
  );
};
