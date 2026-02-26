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
  problem:   { start: 0,    duration: 120 },
  enter:     { start: 120,  duration: 90 },
  pipeline:  { start: 210,  duration: 210 },
  dashboard: { start: 420,  duration: 150 },
  results:   { start: 570,  duration: 150 },
  rich:      { start: 720,  duration: 150 },
  cta:       { start: 870,  duration: 30 },
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
