import { AbsoluteFill, Sequence } from "remotion";
import { COLORS } from "./lib/colors";

const SCENE = {
  problem:   { start: 0,    duration: 240 },
  enter:     { start: 240,  duration: 180 },
  pipeline:  { start: 420,  duration: 420 },
  dashboard: { start: 840,  duration: 300 },
  results:   { start: 1140, duration: 300 },
  rich:      { start: 1440, duration: 300 },
  cta:       { start: 1740, duration: 60 },
} as const;

export const DemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      <Sequence from={SCENE.problem.start} durationInFrames={SCENE.problem.duration} name="The Problem">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.text, fontSize: 48 }}>
          Scene 1: The Problem
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.enter.start} durationInFrames={SCENE.enter.duration} name="Enter Syntrix">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.cyan, fontSize: 48 }}>
          Scene 2: Enter Syntrix
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.pipeline.start} durationInFrames={SCENE.pipeline.duration} name="The Pipeline">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.blue, fontSize: 48 }}>
          Scene 3: The Pipeline
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.dashboard.start} durationInFrames={SCENE.dashboard.duration} name="The Dashboard">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.magenta, fontSize: 48 }}>
          Scene 4: The Dashboard
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.results.start} durationInFrames={SCENE.results.duration} name="The Results">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.green, fontSize: 48 }}>
          Scene 5: The Results
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.rich.start} durationInFrames={SCENE.rich.duration} name="Getting Rich">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.gold, fontSize: 48 }}>
          Scene 6: Getting Rich
        </AbsoluteFill>
      </Sequence>
      <Sequence from={SCENE.cta.start} durationInFrames={SCENE.cta.duration} name="CTA">
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", color: COLORS.text, fontSize: 48 }}>
          Scene 7: CTA
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
