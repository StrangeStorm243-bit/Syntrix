import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
} from "remotion";
import { COLORS } from "../lib/colors";
import { HockeyStick } from "../components/HockeyStick";
import { MoneyRain } from "../components/MoneyRain";
import { ParticleBurst } from "../components/ParticleBurst";

const formatRevenue = (n: number): string => {
  if (n >= 1_000_000) {
    return "$1,000,000";
  }
  if (n >= 1_000) {
    const k = Math.round(n / 1_000);
    return `$${k.toLocaleString()}K`;
  }
  return `$${Math.round(n).toLocaleString()}`;
};

export const GettingRich: React.FC = () => {
  const frame = useCurrentFrame();

  // White flash for first 5 frames
  const flashOpacity = interpolate(frame, [0, 5], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Gold radial glow builds
  const goldIntensity = interpolate(frame, [0, 125], [0.05, 0.3], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Screen shake increases over frames 50-140
  const shakeAmplitude = interpolate(frame, [50, 140], [0, 6], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shakeX = Math.sin(frame * 1.7) * shakeAmplitude;
  const shakeY = Math.cos(frame * 2.3) * shakeAmplitude;

  // Revenue counter: exponential easing ($0 -> $1M)
  const counterProgress = interpolate(frame, [15, 130], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const revenue = Math.pow(counterProgress, 4) * 1_000_000;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Gold radial glow */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${COLORS.goldBright}${Math.round(goldIntensity * 255)
            .toString(16)
            .padStart(2, "0")} 0%, transparent 70%)`,
        }}
      />

      {/* Shaking container */}
      <AbsoluteFill
        style={{
          transform: `translate(${shakeX}px, ${shakeY}px)`,
        }}
      >
        {/* Revenue counter at top */}
        <div
          style={{
            position: "absolute",
            top: 80,
            left: 0,
            right: 0,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 18,
              fontWeight: 600,
              fontFamily: "system-ui, sans-serif",
              color: COLORS.goldBright,
              textTransform: "uppercase",
              letterSpacing: 4,
              marginBottom: 8,
            }}
          >
            Monthly Recurring Revenue
          </div>
          <div
            style={{
              fontSize: 80,
              fontWeight: 800,
              fontFamily: "monospace",
              color: COLORS.moneyGreen,
              textShadow: `0 0 40px ${COLORS.moneyGreen}66`,
            }}
          >
            {formatRevenue(revenue)}
          </div>
        </div>

        {/* Hockey stick chart */}
        <HockeyStick startFrame={10} duration={120} />

        {/* Money rain */}
        <MoneyRain count={70} startFrame={8} />
      </AbsoluteFill>

      {/* Particle bursts at increasing intensity */}
      <ParticleBurst
        triggerFrame={60}
        count={30}
        color={COLORS.goldBright}
        radius={400}
        duration={23}
        cx={960}
        cy={540}
      />
      <ParticleBurst
        triggerFrame={100}
        count={45}
        color={COLORS.moneyGreen}
        radius={500}
        duration={25}
        cx={960}
        cy={540}
      />
      <ParticleBurst
        triggerFrame={130}
        count={60}
        color={COLORS.goldBright}
        radius={600}
        duration={20}
        cx={960}
        cy={540}
      />

      {/* White flash overlay */}
      <AbsoluteFill
        style={{
          backgroundColor: COLORS.white,
          opacity: flashOpacity,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
