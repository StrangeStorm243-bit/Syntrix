import { AbsoluteFill, Sequence } from "remotion";
import { COLORS } from "./lib/colors";
import { TheProblem } from "./scenes/TheProblem";
import { EnterSyntrix } from "./scenes/EnterSyntrix";
import { ThePipeline } from "./scenes/ThePipeline";
import { TheDashboard } from "./scenes/TheDashboard";
import { TheResults } from "./scenes/TheResults";
import { GettingRich } from "./scenes/GettingRich";
import { CTA } from "./scenes/CTA";

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
        <TheProblem />
      </Sequence>
      <Sequence from={SCENE.enter.start} durationInFrames={SCENE.enter.duration} name="Enter Syntrix">
        <EnterSyntrix />
      </Sequence>
      <Sequence from={SCENE.pipeline.start} durationInFrames={SCENE.pipeline.duration} name="The Pipeline">
        <ThePipeline />
      </Sequence>
      <Sequence from={SCENE.dashboard.start} durationInFrames={SCENE.dashboard.duration} name="The Dashboard">
        <TheDashboard />
      </Sequence>
      <Sequence from={SCENE.results.start} durationInFrames={SCENE.results.duration} name="The Results">
        <TheResults />
      </Sequence>
      <Sequence from={SCENE.rich.start} durationInFrames={SCENE.rich.duration} name="Getting Rich">
        <GettingRich />
      </Sequence>
      <Sequence from={SCENE.cta.start} durationInFrames={SCENE.cta.duration} name="CTA">
        <CTA />
      </Sequence>
    </AbsoluteFill>
  );
};
