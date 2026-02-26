import React from "react";
import { useCurrentFrame, AbsoluteFill } from "remotion";

interface ScanlinesProps {
  opacity?: number;
  lineHeight?: number;
}

export const Scanlines: React.FC<ScanlinesProps> = ({
  opacity = 0.06,
  lineHeight = 3,
}) => {
  const frame = useCurrentFrame();

  const offset = (frame * 0.5) % (lineHeight * 2);

  return (
    <AbsoluteFill
      style={{
        background: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent ${lineHeight}px,
          rgba(0, 0, 0, ${opacity}) ${lineHeight}px,
          rgba(0, 0, 0, ${opacity}) ${lineHeight * 2}px
        )`,
        backgroundPositionY: offset,
        pointerEvents: "none",
      }}
    />
  );
};
