import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { COLORS } from "../lib/colors";
import { TweetBubble } from "../components/TweetBubble";
import { Scanlines } from "../components/Scanlines";

const TWEETS = [
  {
    handle: "@frustrated_dev",
    text: "Code review is killing our velocity. Every PR takes 3 days.",
    from: "left" as const,
    delay: 10,
    x: -320,
    y: -180,
  },
  {
    handle: "@startup_sarah",
    text: "Bugs keep slipping through PRs... we need better tooling.",
    from: "right" as const,
    delay: 30,
    x: 280,
    y: -80,
  },
  {
    handle: "@ctojennifer",
    text: "Who even reads our tweets? Feels like shouting into the void.",
    from: "top" as const,
    delay: 55,
    x: -100,
    y: 40,
  },
  {
    handle: "@devops_mike",
    text: "We're losing deals because we can't find leads fast enough.",
    from: "left" as const,
    delay: 75,
    x: 250,
    y: 160,
  },
  {
    handle: "@indie_maker",
    text: "Spent 4 hours manually searching Twitter for potential users. Got 2 leads.",
    from: "right" as const,
    delay: 95,
    x: -280,
    y: 250,
  },
];

export const TheProblem: React.FC = () => {
  const frame = useCurrentFrame();

  // Red ambient glow builds over first 180 frames
  const glowIntensity = interpolate(frame, [0, 180], [0, 0.3], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Headline fade in at frame 160-200
  const headlineOpacity = interpolate(frame, [160, 200], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Red ambient glow */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${COLORS.problemRed}${Math.round(glowIntensity * 255)
            .toString(16)
            .padStart(2, "0")} 0%, transparent 70%)`,
        }}
      />

      {/* Tweet bubbles */}
      {TWEETS.map((tweet) => (
        <TweetBubble
          key={tweet.handle}
          handle={tweet.handle}
          text={tweet.text}
          from={tweet.from}
          delay={tweet.delay}
          x={tweet.x}
          y={tweet.y}
          glowColor={COLORS.problemRed}
        />
      ))}

      {/* Headline */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: headlineOpacity,
          fontSize: 42,
          fontWeight: 700,
          fontFamily: "system-ui, sans-serif",
          color: COLORS.text,
        }}
      >
        Your customers are crying for help on{" "}
        <span style={{ color: COLORS.twitterBlue }}>X</span>.
      </div>

      {/* Scanlines overlay */}
      <Scanlines opacity={0.04} />
    </AbsoluteFill>
  );
};
