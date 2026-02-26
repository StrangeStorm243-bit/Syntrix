# Remotion Demo Video Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 60-second programmatic demo video in a standalone `video/` Remotion project and embed it top-center on the syntrix.app landing page via `@remotion/player`.

**Architecture:** Standalone `video/` directory at repo root with its own `package.json`. Seven scene components composed into a master `DemoVideo.tsx` via Remotion `<Sequence>`. The landing page (`landing/`) imports `@remotion/player` and wraps the rendered MP4 (or live composition) in a `<DemoEmbed>` section placed between Hero and TrustBar.

**Tech Stack:** remotion v4.0.399, @remotion/cli v4.0.399, @remotion/player v4.0.399, React 19, TypeScript

---

## Task 1: Scaffold the Remotion Project

**Files:**
- Create: `video/package.json`
- Create: `video/tsconfig.json`
- Create: `video/src/index.ts`
- Create: `video/src/Root.tsx`
- Create: `video/src/DemoVideo.tsx`
- Create: `video/src/lib/colors.ts`
- Create: `video/src/lib/easing.ts`

**Step 1: Create `video/package.json`**

```json
{
  "name": "syntrix-demo-video",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "studio": "remotion studio src/index.ts",
    "render": "remotion render src/index.ts DemoVideo out/demo-1080p.mp4",
    "render:720": "remotion render src/index.ts DemoVideo out/demo-720p.mp4 --scale=0.667",
    "render:square": "remotion render src/index.ts DemoVideoSquare out/demo-square.mp4",
    "render:vertical": "remotion render src/index.ts DemoVideoVertical out/demo-vertical.mp4"
  },
  "dependencies": {
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "remotion": "4.0.399",
    "@remotion/cli": "4.0.399"
  },
  "devDependencies": {
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "typescript": "^5"
  }
}
```

**Step 2: Create `video/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2018",
    "module": "commonjs",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "outDir": "./dist"
  },
  "include": ["src/**/*.ts", "src/**/*.tsx"]
}
```

**Step 3: Create `video/src/lib/colors.ts`**

```ts
// Brand palette from design-system/syntrix/MASTER.md
export const COLORS = {
  // Core
  base: "#0F172A",        // slate-900 — dark backgrounds
  surface: "#1E293B",     // slate-800 — cards, panels
  text: "#F8FAFC",        // slate-50 — primary text
  textMuted: "#94A3B8",   // slate-400 — secondary text

  // Aurora accents
  cyan: "#06B6D4",
  blue: "#3B82F6",
  magenta: "#D946EF",
  green: "#22C55E",

  // Twitter
  twitterBlue: "#1DA1F2",

  // Scene-specific
  problemRed: "#EF4444",
  gold: "#F59E0B",
  goldBright: "#FBBF24",
  moneyGreen: "#10B981",

  // Neutral
  white: "#FFFFFF",
  black: "#000000",
} as const;
```

**Step 4: Create `video/src/lib/easing.ts`**

```ts
import type { SpringConfig } from "remotion";

// Snappy overshoot for logo slams, stamps
export const SPRING_SNAPPY: SpringConfig = {
  damping: 12,
  mass: 0.5,
  stiffness: 200,
};

// Gentle float for cards, notifications
export const SPRING_GENTLE: SpringConfig = {
  damping: 15,
  mass: 1,
  stiffness: 100,
};

// Heavy slam for dramatic impacts
export const SPRING_SLAM: SpringConfig = {
  damping: 8,
  mass: 2,
  stiffness: 300,
};

// Quick no-overshoot for counters, progress
export const SPRING_CRISP: SpringConfig = {
  damping: 200,
  mass: 1,
  stiffness: 200,
};
```

**Step 5: Create `video/src/DemoVideo.tsx` (empty shell)**

```tsx
import { AbsoluteFill, Sequence } from "remotion";
import { COLORS } from "./lib/colors";

// Scene durations in frames (30fps)
const SCENE = {
  problem:   { start: 0,    duration: 240 },  // 0s–8s
  enter:     { start: 240,  duration: 180 },  // 8s–14s
  pipeline:  { start: 420,  duration: 420 },  // 14s–28s
  dashboard: { start: 840,  duration: 300 },  // 28s–38s
  results:   { start: 1140, duration: 300 },  // 38s–48s
  rich:      { start: 1440, duration: 300 },  // 48s–58s
  cta:       { start: 1740, duration: 60 },   // 58s–60s
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
```

**Step 6: Create `video/src/Root.tsx`**

```tsx
import { Composition } from "remotion";
import { DemoVideo } from "./DemoVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DemoVideo"
        component={DemoVideo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
```

**Step 7: Create `video/src/index.ts`**

```ts
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
```

**Step 8: Install dependencies**

Run:
```bash
cd video && npm install
```

**Step 9: Verify in Remotion Studio**

Run:
```bash
cd video && npx remotion studio src/index.ts
```

Expected: Studio opens in browser, shows "DemoVideo" composition with 7 placeholder scenes visible in timeline. Each scene shows its label text at the correct time.

**Step 10: Commit**

```bash
git add video/
git commit -m "feat(video): scaffold Remotion project with placeholder scenes"
```

---

## Task 2: Reusable Components — TweetBubble + Typewriter

**Files:**
- Create: `video/src/components/TweetBubble.tsx`
- Create: `video/src/components/Typewriter.tsx`

**Step 1: Create `video/src/components/TweetBubble.tsx`**

A tweet card that flies in from an edge with spring physics. Shows avatar circle, handle, and tweet text.

```tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_GENTLE } from "../lib/easing";

interface TweetBubbleProps {
  handle: string;
  text: string;
  /** Delay in frames before this tweet appears */
  delay?: number;
  /** Starting position offscreen: "left" | "right" | "top" | "bottom" */
  from?: "left" | "right" | "top" | "bottom";
  /** Final X position (px from center) */
  x?: number;
  /** Final Y position (px from center) */
  y?: number;
  /** Glow color */
  glowColor?: string;
}

export const TweetBubble: React.FC<TweetBubbleProps> = ({
  handle,
  text,
  delay = 0,
  from = "left",
  x = 0,
  y = 0,
  glowColor = COLORS.twitterBlue,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ fps, frame: frame - delay, config: SPRING_GENTLE });

  const offscreen: Record<string, { tx: number; ty: number }> = {
    left: { tx: -1200, ty: 0 },
    right: { tx: 1200, ty: 0 },
    top: { tx: 0, ty: -800 },
    bottom: { tx: 0, ty: 800 },
  };

  const { tx: startX, ty: startY } = offscreen[from];
  const translateX = interpolate(enter, [0, 1], [startX, x]);
  const translateY = interpolate(enter, [0, 1], [startY, y]);
  const opacity = interpolate(enter, [0, 0.3], [0, 1], { extrapolateRight: "clamp" });
  const rotate = interpolate(enter, [0, 1], [from === "left" ? -15 : 15, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        transform: `translate(-50%, -50%) translate(${translateX}px, ${translateY}px) rotate(${rotate}deg)`,
        opacity,
        width: 420,
        padding: 20,
        borderRadius: 16,
        backgroundColor: COLORS.surface,
        border: `1px solid ${glowColor}33`,
        boxShadow: `0 0 30px ${glowColor}22`,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 18,
            background: `linear-gradient(135deg, ${glowColor}, ${COLORS.cyan})`,
          }}
        />
        <span style={{ color: COLORS.textMuted, fontSize: 14 }}>{handle}</span>
      </div>
      <p style={{ color: COLORS.text, fontSize: 16, lineHeight: 1.5, margin: 0 }}>{text}</p>
    </div>
  );
};
```

**Step 2: Create `video/src/components/Typewriter.tsx`**

Character-by-character text reveal.

```tsx
import { useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";

interface TypewriterProps {
  text: string;
  /** Frames per character */
  speed?: number;
  /** Frame delay before typing starts */
  delay?: number;
  fontSize?: number;
  color?: string;
  fontFamily?: string;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  speed = 2,
  delay = 0,
  fontSize = 32,
  color = COLORS.text,
  fontFamily = "monospace",
}) => {
  const frame = useCurrentFrame();
  const charsToShow = Math.max(0, Math.floor((frame - delay) / speed));
  const visibleText = text.slice(0, charsToShow);
  const showCursor = frame > delay && charsToShow < text.length;

  return (
    <span style={{ fontSize, color, fontFamily, whiteSpace: "pre" }}>
      {visibleText}
      {showCursor && (
        <span style={{ opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0, color: COLORS.cyan }}>▊</span>
      )}
    </span>
  );
};
```

**Step 3: Verify in Remotion Studio**

Temporarily import TweetBubble into the Scene 1 placeholder in `DemoVideo.tsx` to see it animate in. Remove after verification.

**Step 4: Commit**

```bash
git add video/src/components/TweetBubble.tsx video/src/components/Typewriter.tsx
git commit -m "feat(video): add TweetBubble and Typewriter components"
```

---

## Task 3: Reusable Components — Counter + Scanlines + ParticleBurst

**Files:**
- Create: `video/src/components/Counter.tsx`
- Create: `video/src/components/Scanlines.tsx`
- Create: `video/src/components/ParticleBurst.tsx`

**Step 1: Create `video/src/components/Counter.tsx`**

Animated number counter that interpolates between values.

```tsx
import { interpolate, useCurrentFrame } from "remotion";

interface CounterProps {
  from?: number;
  to: number;
  /** Start frame (relative to parent Sequence) */
  startAt?: number;
  /** Duration of the count animation in frames */
  duration?: number;
  prefix?: string;
  suffix?: string;
  fontSize?: number;
  color?: string;
  formatFn?: (n: number) => string;
}

const defaultFormat = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}K`;
  return Math.round(n).toLocaleString();
};

export const Counter: React.FC<CounterProps> = ({
  from = 0,
  to,
  startAt = 0,
  duration = 60,
  prefix = "",
  suffix = "",
  fontSize = 64,
  color = "#FFFFFF",
  formatFn = defaultFormat,
}) => {
  const frame = useCurrentFrame();
  const value = interpolate(frame, [startAt, startAt + duration], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <span style={{ fontSize, color, fontFamily: "monospace", fontWeight: 700 }}>
      {prefix}{formatFn(value)}{suffix}
    </span>
  );
};
```

**Step 2: Create `video/src/components/Scanlines.tsx`**

CRT scanline overlay for cyberpunk scenes.

```tsx
import { AbsoluteFill, useCurrentFrame } from "remotion";

interface ScanlinesProps {
  opacity?: number;
  lineHeight?: number;
}

export const Scanlines: React.FC<ScanlinesProps> = ({
  opacity = 0.06,
  lineHeight = 3,
}) => {
  const frame = useCurrentFrame();
  // Slow vertical scroll for realism
  const offset = (frame * 0.5) % (lineHeight * 2);

  return (
    <AbsoluteFill
      style={{
        background: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent ${lineHeight}px,
          rgba(0,0,0,${opacity}) ${lineHeight}px,
          rgba(0,0,0,${opacity}) ${lineHeight * 2}px
        )`,
        backgroundPositionY: offset,
        pointerEvents: "none",
      }}
    />
  );
};
```

**Step 3: Create `video/src/components/ParticleBurst.tsx`**

Radial particle explosion from a center point.

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface ParticleBurstProps {
  /** Frame to trigger the burst */
  triggerFrame?: number;
  count?: number;
  color?: string;
  /** Max radius particles travel */
  radius?: number;
  /** Duration of burst in frames */
  duration?: number;
  /** Center X (0 = left, 1920 = right) */
  cx?: number;
  /** Center Y (0 = top, 1080 = bottom) */
  cy?: number;
}

export const ParticleBurst: React.FC<ParticleBurstProps> = ({
  triggerFrame = 0,
  count = 40,
  color = "#06B6D4",
  radius = 400,
  duration = 30,
  cx = 960,
  cy = 540,
}) => {
  const frame = useCurrentFrame();
  const t = frame - triggerFrame;
  if (t < 0 || t > duration) return null;

  const progress = t / duration;
  const globalOpacity = interpolate(progress, [0, 0.3, 1], [0, 1, 0]);

  // Deterministic random using index as seed
  const particles = Array.from({ length: count }, (_, i) => {
    const angle = (i / count) * Math.PI * 2 + (i * 0.618);
    const speed = 0.5 + (((i * 7 + 3) % 10) / 10) * 0.5; // 0.5–1.0
    const size = 3 + (i % 5);
    const dist = progress * radius * speed;
    const x = cx + Math.cos(angle) * dist;
    const y = cy + Math.sin(angle) * dist;
    return { x, y, size };
  });

  return (
    <AbsoluteFill style={{ opacity: globalOpacity, pointerEvents: "none" }}>
      {particles.map((p, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            backgroundColor: color,
            boxShadow: `0 0 ${p.size * 2}px ${color}`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};
```

**Step 4: Verify in Remotion Studio**

Spot-check each component by temporarily rendering them in DemoVideo.tsx.

**Step 5: Commit**

```bash
git add video/src/components/Counter.tsx video/src/components/Scanlines.tsx video/src/components/ParticleBurst.tsx
git commit -m "feat(video): add Counter, Scanlines, and ParticleBurst components"
```

---

## Task 4: Reusable Components — Notification + PipelineStage + MoneyRain + HockeyStick

**Files:**
- Create: `video/src/components/Notification.tsx`
- Create: `video/src/components/PipelineStage.tsx`
- Create: `video/src/components/MoneyRain.tsx`
- Create: `video/src/components/HockeyStick.tsx`

**Step 1: Create `video/src/components/Notification.tsx`**

Slide-in notification row with spring pop.

```tsx
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SNAPPY } from "../lib/easing";

interface NotificationProps {
  text: string;
  color?: string;
  icon?: string;
  delay?: number;
  y?: number;
}

export const Notification: React.FC<NotificationProps> = ({
  text,
  color = COLORS.cyan,
  icon = "→",
  delay = 0,
  y = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ fps, frame: frame - delay, config: SPRING_SNAPPY });
  const translateX = interpolate(enter, [0, 1], [600, 0]);
  const opacity = interpolate(enter, [0, 0.5], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(enter, [0, 1], [0.8, 1]);

  return (
    <div
      style={{
        position: "absolute",
        right: 80,
        top: 200 + y,
        transform: `translateX(${translateX}px) scale(${scale})`,
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 20px",
        borderRadius: 12,
        backgroundColor: `${COLORS.surface}ee`,
        border: `1px solid ${color}44`,
        boxShadow: `0 0 20px ${color}22`,
        fontFamily: "system-ui, sans-serif",
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ color, fontSize: 18 }}>{icon}</span>
      <span style={{ color: COLORS.text, fontSize: 16 }}>{text}</span>
    </div>
  );
};
```

**Step 2: Create `video/src/components/PipelineStage.tsx`**

A single pipeline node that glows on when activated.

```tsx
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SNAPPY } from "../lib/easing";

interface PipelineStageProps {
  label: string;
  icon: string;
  color: string;
  /** Frame at which this stage activates */
  activateAt?: number;
  x: number;
  y: number;
}

export const PipelineStage: React.FC<PipelineStageProps> = ({
  label,
  icon,
  color,
  activateAt = 0,
  x,
  y,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ fps, frame: frame - activateAt, config: SPRING_SNAPPY });
  const scale = interpolate(enter, [0, 1], [0, 1]);
  const glowOpacity = interpolate(enter, [0, 1], [0, 0.6]);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 16,
          backgroundColor: `${color}22`,
          border: `2px solid ${color}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          boxShadow: `0 0 ${20 * glowOpacity}px ${color}`,
        }}
      >
        {icon}
      </div>
      <span style={{ color: COLORS.text, fontSize: 13, fontFamily: "system-ui, sans-serif", fontWeight: 600 }}>
        {label}
      </span>
    </div>
  );
};
```

**Step 3: Create `video/src/components/MoneyRain.tsx`**

Dollar signs and confetti raining from the top.

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface MoneyRainProps {
  count?: number;
  startFrame?: number;
}

const SYMBOLS = ["$", "💰", "💵", "🤑", "$", "$", "$", "💸"];

export const MoneyRain: React.FC<MoneyRainProps> = ({
  count = 60,
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;
  if (t < 0) return null;

  const particles = Array.from({ length: count }, (_, i) => {
    // Deterministic "random" per particle
    const seed1 = ((i * 127 + 53) % 100) / 100;
    const seed2 = ((i * 71 + 17) % 100) / 100;
    const seed3 = ((i * 43 + 89) % 100) / 100;

    const x = seed1 * 1920;
    const speed = 4 + seed2 * 6; // px per frame
    const delay = seed3 * 40;    // stagger start
    const symbol = SYMBOLS[i % SYMBOLS.length];
    const size = 20 + seed2 * 30;
    const rotation = seed1 * 360 + t * (seed2 > 0.5 ? 3 : -3);

    const localT = t - delay;
    if (localT < 0) return null;

    const yPos = -60 + localT * speed;
    if (yPos > 1140) return null; // offscreen bottom

    const opacity = interpolate(localT, [0, 10], [0, 1], { extrapolateRight: "clamp" });

    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: yPos,
          fontSize: size,
          transform: `rotate(${rotation}deg)`,
          opacity,
          pointerEvents: "none",
        }}
      >
        {symbol}
      </div>
    );
  });

  return <AbsoluteFill style={{ overflow: "hidden" }}>{particles}</AbsoluteFill>;
};
```

**Step 4: Create `video/src/components/HockeyStick.tsx`**

Exponential revenue chart that animates and breaks through the frame.

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";

interface HockeyStickProps {
  startFrame?: number;
  duration?: number;
}

export const HockeyStick: React.FC<HockeyStickProps> = ({
  startFrame = 0,
  duration = 180,
}) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;
  if (t < 0) return null;

  const progress = Math.min(1, t / duration);
  const numPoints = Math.floor(progress * 50);

  // Exponential curve
  const points: Array<{ x: number; y: number }> = [];
  const chartX = 200;
  const chartW = 800;
  const chartY = 800;
  const chartH = 600;

  for (let i = 0; i <= numPoints; i++) {
    const pct = i / 50;
    const x = chartX + pct * chartW;
    // Exponential: slow start, explosive end
    const val = Math.pow(pct, 3.5);
    const y = chartY - val * chartH;
    points.push({ x, y });
  }

  if (points.length < 2) return null;

  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");

  // Fill area under curve
  const fillD = pathD + ` L ${points[points.length - 1].x} ${chartY} L ${chartX} ${chartY} Z`;

  return (
    <AbsoluteFill>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75, 1].map((pct) => (
          <line
            key={pct}
            x1={chartX}
            y1={chartY - pct * chartH}
            x2={chartX + chartW}
            y2={chartY - pct * chartH}
            stroke={COLORS.textMuted}
            strokeOpacity={0.15}
            strokeDasharray="4 4"
          />
        ))}
        {/* Fill */}
        <path d={fillD} fill={`${COLORS.moneyGreen}22`} />
        {/* Line */}
        <path d={pathD} fill="none" stroke={COLORS.moneyGreen} strokeWidth={4} strokeLinecap="round" />
        {/* Glow line */}
        <path d={pathD} fill="none" stroke={COLORS.moneyGreen} strokeWidth={12} strokeLinecap="round" opacity={0.3} />
        {/* Tip dot */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].x}
            cy={points[points.length - 1].y}
            r={8}
            fill={COLORS.moneyGreen}
          >
            <animate attributeName="r" values="6;10;6" dur="0.5s" repeatCount="indefinite" />
          </circle>
        )}
        {/* Y axis labels */}
        <text x={chartX - 20} y={chartY} fill={COLORS.textMuted} fontSize={14} textAnchor="end" dominantBaseline="middle">$0</text>
        <text x={chartX - 20} y={chartY - chartH} fill={COLORS.moneyGreen} fontSize={14} textAnchor="end" dominantBaseline="middle">$1M</text>
        {/* Label */}
        <text x={chartX + chartW / 2} y={chartY + 50} fill={COLORS.text} fontSize={20} textAnchor="middle" fontFamily="system-ui, sans-serif" fontWeight="600">
          Monthly Recurring Revenue
        </text>
      </svg>
    </AbsoluteFill>
  );
};
```

**Step 5: Commit**

```bash
git add video/src/components/Notification.tsx video/src/components/PipelineStage.tsx video/src/components/MoneyRain.tsx video/src/components/HockeyStick.tsx
git commit -m "feat(video): add Notification, PipelineStage, MoneyRain, and HockeyStick components"
```

---

## Task 5: Scene 1 — The Problem

**Files:**
- Create: `video/src/scenes/TheProblem.tsx`
- Modify: `video/src/DemoVideo.tsx` — replace Scene 1 placeholder

**Step 1: Create `video/src/scenes/TheProblem.tsx`**

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";
import { TweetBubble } from "../components/TweetBubble";
import { Scanlines } from "../components/Scanlines";

const TWEETS = [
  { handle: "@frustrated_dev", text: "Code review is killing our velocity. Every PR takes 3 days.", from: "left" as const, delay: 10, x: -320, y: -180 },
  { handle: "@startup_sarah", text: "Bugs keep slipping through PRs... we need better tooling.", from: "right" as const, delay: 30, x: 280, y: -80 },
  { handle: "@ctojennifer", text: "Who even reads our tweets? Feels like shouting into the void.", from: "top" as const, delay: 55, x: -100, y: 40 },
  { handle: "@devops_mike", text: "We're losing deals because we can't find leads fast enough.", from: "left" as const, delay: 75, x: 250, y: 160 },
  { handle: "@indie_maker", text: "Spent 4 hours manually searching Twitter for potential users. Got 2 leads.", from: "right" as const, delay: 95, x: -280, y: 250 },
];

export const TheProblem: React.FC = () => {
  const frame = useCurrentFrame();

  // Red glow intensifies over time
  const glowIntensity = interpolate(frame, [0, 180], [0, 0.3], { extrapolateRight: "clamp" });

  // Headline fades in at the end
  const headlineOpacity = interpolate(frame, [160, 200], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const headlineY = interpolate(frame, [160, 200], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Red ambient glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 50% 50%, ${COLORS.problemRed}${Math.round(glowIntensity * 255).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
        }}
      />

      {/* Tweets */}
      {TWEETS.map((tweet, i) => (
        <TweetBubble
          key={i}
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
          width: "100%",
          textAlign: "center",
          opacity: headlineOpacity,
          transform: `translateY(${headlineY}px)`,
        }}
      >
        <h2 style={{ color: COLORS.text, fontSize: 42, fontFamily: "system-ui, sans-serif", fontWeight: 700, margin: 0 }}>
          Your customers are crying for help on{" "}
          <span style={{ color: COLORS.twitterBlue }}>X</span>.
        </h2>
      </div>

      <Scanlines opacity={0.04} />
    </AbsoluteFill>
  );
};
```

**Step 2: Update `video/src/DemoVideo.tsx`**

Replace the Scene 1 placeholder `<AbsoluteFill>` with:
```tsx
import { TheProblem } from "./scenes/TheProblem";
// ...
<Sequence from={SCENE.problem.start} durationInFrames={SCENE.problem.duration} name="The Problem">
  <TheProblem />
</Sequence>
```

**Step 3: Verify in Remotion Studio**

Run: `cd video && npm run studio`
Expected: Scene 1 shows 5 tweets flying in from edges, red glow building, headline fading in at ~6s mark.

**Step 4: Commit**

```bash
git add video/src/scenes/TheProblem.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 1 — The Problem with animated tweet bubbles"
```

---

## Task 6: Scene 2 — Enter Syntrix

**Files:**
- Create: `video/src/scenes/EnterSyntrix.tsx`
- Modify: `video/src/DemoVideo.tsx` — replace Scene 2 placeholder

**Step 1: Create `video/src/scenes/EnterSyntrix.tsx`**

```tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SLAM } from "../lib/easing";
import { Typewriter } from "../components/Typewriter";
import { ParticleBurst } from "../components/ParticleBurst";

export const EnterSyntrix: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Aurora gradient wipe (first 15 frames)
  const wipeProgress = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  // Logo slam at frame 15
  const logoSpring = spring({ fps, frame: frame - 15, config: SPRING_SLAM });
  const logoScale = interpolate(logoSpring, [0, 1], [3, 1]);
  const logoOpacity = interpolate(logoSpring, [0, 0.2], [0, 1], { extrapolateRight: "clamp" });

  // Subtext fade
  const subtextOpacity = interpolate(frame, [100, 120], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Aurora gradient background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at 50% 40%, ${COLORS.cyan}15 0%, ${COLORS.magenta}10 50%, transparent 80%)`,
          opacity: wipeProgress,
        }}
      />

      {/* Logo */}
      <div
        style={{
          position: "absolute",
          top: "35%",
          width: "100%",
          textAlign: "center",
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
        }}
      >
        <h1
          style={{
            fontSize: 96,
            fontWeight: 800,
            fontFamily: "system-ui, sans-serif",
            background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.magenta})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            margin: 0,
            letterSpacing: -2,
          }}
        >
          Syntrix
        </h1>
      </div>

      {/* Particle burst on logo impact */}
      <ParticleBurst triggerFrame={20} count={50} color={COLORS.cyan} radius={500} duration={40} />

      {/* Tagline typewriter */}
      <div style={{ position: "absolute", top: "52%", width: "100%", textAlign: "center" }}>
        <Typewriter text="Find.  Engage.  Convert." delay={40} speed={3} fontSize={40} color={COLORS.text} />
      </div>

      {/* Subtext */}
      <div
        style={{
          position: "absolute",
          top: "62%",
          width: "100%",
          textAlign: "center",
          opacity: subtextOpacity,
        }}
      >
        <p style={{ color: COLORS.textMuted, fontSize: 22, fontFamily: "system-ui, sans-serif", margin: 0 }}>
          Open-source AI outreach — self-hosted, human-approved.
        </p>
      </div>
    </AbsoluteFill>
  );
};
```

**Step 2: Wire into DemoVideo.tsx** — replace Scene 2 placeholder.

**Step 3: Verify in Remotion Studio**

Expected: Aurora gradient appears, logo slams in with bounce, particles burst, tagline types out, subtext fades.

**Step 4: Commit**

```bash
git add video/src/scenes/EnterSyntrix.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 2 — Enter Syntrix with logo slam and typewriter"
```

---

## Task 7: Scene 3 — The Pipeline

**Files:**
- Create: `video/src/scenes/ThePipeline.tsx`
- Modify: `video/src/DemoVideo.tsx` — replace Scene 3 placeholder

**Step 1: Create `video/src/scenes/ThePipeline.tsx`**

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";
import { PipelineStage } from "../components/PipelineStage";
import { Scanlines } from "../components/Scanlines";

const STAGES = [
  { label: "Collect",   icon: "🔍", color: COLORS.cyan },
  { label: "Normalize", icon: "📄", color: COLORS.cyan },
  { label: "Judge",     icon: "⚖️", color: COLORS.blue },
  { label: "Score",     icon: "📊", color: COLORS.blue },
  { label: "Draft",     icon: "✏️", color: COLORS.magenta },
  { label: "Approve",   icon: "✅", color: COLORS.green },
  { label: "Send",      icon: "🚀", color: COLORS.magenta },
  { label: "DM",        icon: "💬", color: COLORS.magenta },
];

const STAGE_INTERVAL = 45; // frames between each stage lighting up

export const ThePipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const stageCount = STAGES.length;
  const totalWidth = 1600;
  const startX = (1920 - totalWidth) / 2;
  const stageSpacing = totalWidth / (stageCount - 1);
  const y = 480;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Subtle grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `linear-gradient(${COLORS.textMuted}08 1px, transparent 1px), linear-gradient(90deg, ${COLORS.textMuted}08 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      {/* Section heading */}
      <div style={{ position: "absolute", top: 120, width: "100%", textAlign: "center" }}>
        <h2 style={{ color: COLORS.text, fontSize: 40, fontFamily: "system-ui, sans-serif", fontWeight: 700, margin: 0 }}>
          From signal to sent —{" "}
          <span style={{ color: COLORS.cyan }}>in one pipeline</span>
        </h2>
        <p style={{ color: COLORS.textMuted, fontSize: 20, marginTop: 12, fontFamily: "system-ui, sans-serif" }}>
          8 stages. Fully configurable. Human-approved at every step.
        </p>
      </div>

      {/* Connecting lines */}
      <svg width={1920} height={1080} style={{ position: "absolute", top: 0, left: 0 }}>
        {STAGES.map((_, i) => {
          if (i === stageCount - 1) return null;
          const x1 = startX + i * stageSpacing + 32;
          const x2 = startX + (i + 1) * stageSpacing + 32;
          const lineFrame = (i + 1) * STAGE_INTERVAL;
          const lineProgress = interpolate(frame, [lineFrame, lineFrame + 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <line
              key={i}
              x1={x1}
              y1={y + 32}
              x2={x1 + (x2 - x1) * lineProgress}
              y2={y + 32}
              stroke={STAGES[i].color}
              strokeWidth={2}
              strokeOpacity={0.5}
            />
          );
        })}
      </svg>

      {/* Pipeline stages */}
      {STAGES.map((stage, i) => (
        <PipelineStage
          key={stage.label}
          label={stage.label}
          icon={stage.icon}
          color={stage.color}
          activateAt={i * STAGE_INTERVAL + 20}
          x={startX + i * stageSpacing}
          y={y}
        />
      ))}

      {/* Human-in-the-loop callout */}
      {frame > STAGE_INTERVAL * 5 + 40 && (
        <div
          style={{
            position: "absolute",
            bottom: 120,
            width: "100%",
            textAlign: "center",
            opacity: interpolate(frame, [STAGE_INTERVAL * 5 + 40, STAGE_INTERVAL * 5 + 60], [0, 1], {
              extrapolateRight: "clamp",
            }),
          }}
        >
          <span
            style={{
              color: COLORS.green,
              fontSize: 20,
              fontFamily: "system-ui, sans-serif",
              padding: "8px 20px",
              borderRadius: 8,
              border: `1px solid ${COLORS.green}44`,
              backgroundColor: `${COLORS.green}11`,
            }}
          >
            ✅ Human approves every draft — zero spam, full control
          </span>
        </div>
      )}

      <Scanlines opacity={0.03} />
    </AbsoluteFill>
  );
};
```

**Step 2: Wire into DemoVideo.tsx**

**Step 3: Verify in Remotion Studio**

Expected: Stages appear one by one left-to-right with connecting lines drawing between them.

**Step 4: Commit**

```bash
git add video/src/scenes/ThePipeline.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 3 — The Pipeline with sequential stage activation"
```

---

## Task 8: Scene 4 — The Dashboard

**Files:**
- Create: `video/src/scenes/TheDashboard.tsx`
- Modify: `video/src/DemoVideo.tsx`

**Step 1: Create `video/src/scenes/TheDashboard.tsx`**

A stylized neon dashboard that slides up and animates metric counters.

```tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { Counter } from "../components/Counter";
import { SPRING_GENTLE } from "../lib/easing";

const METRICS = [
  { label: "Collected", value: 1247, color: COLORS.cyan },
  { label: "Relevant",  value: 389,  color: COLORS.blue },
  { label: "Drafted",   value: 87,   color: COLORS.magenta },
  { label: "Sent",      value: 58,   color: COLORS.green },
];

const QUEUE_ROWS = [
  { id: 1, handle: "@techleadSara", draft: "\"Totally feel that — we built...\"", score: 92 },
  { id: 2, handle: "@devops_mike",  draft: "\"Great question — we've been...\"", score: 87 },
  { id: 3, handle: "@ctojennifer",  draft: "\"That's frustrating. We catch...\"", score: 83 },
];

export const TheDashboard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide up
  const slideUp = spring({ fps, frame, config: SPRING_GENTLE });
  const translateY = interpolate(slideUp, [0, 1], [400, 0]);
  const dashOpacity = interpolate(slideUp, [0, 0.3], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      <div
        style={{
          position: "absolute",
          inset: 40,
          transform: `translateY(${translateY}px)`,
          opacity: dashOpacity,
          borderRadius: 20,
          border: `1px solid ${COLORS.cyan}33`,
          backgroundColor: `${COLORS.surface}ee`,
          overflow: "hidden",
          display: "flex",
        }}
      >
        {/* Sidebar */}
        <div
          style={{
            width: 220,
            borderRight: `1px solid ${COLORS.cyan}22`,
            padding: 24,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: COLORS.text, fontFamily: "system-ui, sans-serif" }}>
              Syntrix
            </span>
            <span
              style={{
                fontSize: 10,
                color: COLORS.magenta,
                border: `1px solid ${COLORS.magenta}44`,
                borderRadius: 12,
                padding: "2px 8px",
                fontFamily: "monospace",
              }}
            >
              v0.3
            </span>
          </div>
          {["Dashboard", "Leads", "Queue", "Analytics", "Settings"].map((item, i) => (
            <div
              key={item}
              style={{
                color: i === 0 ? COLORS.cyan : COLORS.textMuted,
                fontSize: 14,
                fontFamily: "system-ui, sans-serif",
                padding: "8px 12px",
                borderRadius: 8,
                backgroundColor: i === 0 ? `${COLORS.cyan}15` : "transparent",
              }}
            >
              {item}
            </div>
          ))}
        </div>

        {/* Main content */}
        <div style={{ flex: 1, padding: 32 }}>
          {/* Metric cards */}
          <div style={{ display: "flex", gap: 20, marginBottom: 32 }}>
            {METRICS.map((m, i) => {
              const cardDelay = 20 + i * 15;
              const cardOpacity = interpolate(frame, [cardDelay, cardDelay + 15], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return (
                <div
                  key={m.label}
                  style={{
                    flex: 1,
                    padding: 20,
                    borderRadius: 12,
                    border: `1px solid ${m.color}33`,
                    backgroundColor: `${m.color}08`,
                    opacity: cardOpacity,
                  }}
                >
                  <div style={{ color: COLORS.textMuted, fontSize: 13, fontFamily: "system-ui, sans-serif", marginBottom: 8 }}>
                    {m.label}
                  </div>
                  <Counter to={m.value} startAt={cardDelay} duration={60} fontSize={36} color={m.color} formatFn={(n) => Math.round(n).toLocaleString()} />
                </div>
              );
            })}
          </div>

          {/* Draft queue */}
          <div style={{ borderRadius: 12, border: `1px solid ${COLORS.textMuted}22`, overflow: "hidden" }}>
            <div
              style={{
                padding: "12px 20px",
                backgroundColor: `${COLORS.surface}`,
                borderBottom: `1px solid ${COLORS.textMuted}22`,
                color: COLORS.text,
                fontSize: 15,
                fontWeight: 600,
                fontFamily: "system-ui, sans-serif",
              }}
            >
              Draft Queue
            </div>
            {QUEUE_ROWS.map((row, i) => {
              const rowDelay = 100 + i * 35;
              const approved = frame > rowDelay + 50;
              const rowOpacity = interpolate(frame, [rowDelay, rowDelay + 15], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return (
                <div
                  key={row.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "14px 20px",
                    borderBottom: `1px solid ${COLORS.textMuted}11`,
                    opacity: rowOpacity,
                    gap: 20,
                    fontFamily: "system-ui, sans-serif",
                  }}
                >
                  <span style={{ color: COLORS.textMuted, fontSize: 14, width: 40 }}>#{row.id}</span>
                  <span style={{ color: COLORS.cyan, fontSize: 14, width: 140 }}>{row.handle}</span>
                  <span style={{ color: COLORS.text, fontSize: 13, flex: 1, opacity: 0.8 }}>{row.draft}</span>
                  <span style={{ color: COLORS.textMuted, fontSize: 13, width: 40 }}>{row.score}</span>
                  <div
                    style={{
                      padding: "4px 14px",
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 600,
                      backgroundColor: approved ? `${COLORS.green}22` : `${COLORS.textMuted}15`,
                      color: approved ? COLORS.green : COLORS.textMuted,
                      border: `1px solid ${approved ? COLORS.green : COLORS.textMuted}33`,
                      transition: "all 0.3s",
                    }}
                  >
                    {approved ? "✓ Approved" : "Pending"}
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
```

**Step 2: Wire into DemoVideo.tsx**

**Step 3: Verify in Remotion Studio**

Expected: Dashboard slides up, metrics count, queue rows appear and get approved one by one.

**Step 4: Commit**

```bash
git add video/src/scenes/TheDashboard.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 4 — The Dashboard with animated metrics and approval queue"
```

---

## Task 9: Scene 5 — The Results

**Files:**
- Create: `video/src/scenes/TheResults.tsx`
- Modify: `video/src/DemoVideo.tsx`

**Step 1: Create `video/src/scenes/TheResults.tsx`**

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";
import { Notification } from "../components/Notification";

const NOTIFICATIONS = [
  { text: "Reply sent to @techleadSara",                  icon: "→", color: COLORS.cyan,    delay: 15 },
  { text: "DM delivered to @devops_mike",                 icon: "✉", color: COLORS.magenta, delay: 50 },
  { text: "@ctojennifer viewed your profile",             icon: "👁", color: COLORS.text,    delay: 80 },
  { text: "New follower: @ctojennifer",                   icon: "+", color: COLORS.green,   delay: 105 },
  { text: "Inbound DM: 'Hey, can we chat about Syntrix?'", icon: "💬", color: COLORS.gold,   delay: 130 },
  { text: "Reply sent to @growthguru",                    icon: "→", color: COLORS.cyan,    delay: 155 },
  { text: "DM delivered to @saas_founder",                icon: "✉", color: COLORS.magenta, delay: 170 },
  { text: "3 new followers this hour",                    icon: "📈", color: COLORS.green,   delay: 185 },
  { text: "Inbound: 'Love what you're building!'",       icon: "💬", color: COLORS.gold,    delay: 195 },
  { text: "Demo request from @enterprise_cto",            icon: "🔥", color: COLORS.gold,    delay: 210 },
  { text: "Pipeline: 12 new high-score leads",            icon: "⚡", color: COLORS.cyan,    delay: 220 },
  { text: "Revenue alert: $2,400 MRR milestone",          icon: "💰", color: COLORS.moneyGreen, delay: 240 },
];

export const TheResults: React.FC = () => {
  const frame = useCurrentFrame();

  // Left side: glowing pipeline animation
  const pulseOpacity = 0.3 + Math.sin(frame * 0.1) * 0.15;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Left panel: Pipeline status */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "45%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          borderRight: `1px solid ${COLORS.cyan}22`,
        }}
      >
        <div
          style={{
            width: 300,
            height: 300,
            borderRadius: "50%",
            border: `2px solid ${COLORS.cyan}44`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 0 ${60 * pulseOpacity}px ${COLORS.cyan}33, inset 0 0 ${40 * pulseOpacity}px ${COLORS.cyan}11`,
          }}
        >
          <span style={{ color: COLORS.cyan, fontSize: 14, fontFamily: "monospace", opacity: 0.7 }}>PIPELINE</span>
          <span style={{ color: COLORS.text, fontSize: 48, fontWeight: 700, fontFamily: "system-ui, sans-serif" }}>
            ACTIVE
          </span>
          <span style={{ color: COLORS.green, fontSize: 16, fontFamily: "monospace", marginTop: 8 }}>
            ● Running
          </span>
        </div>

        <div style={{ marginTop: 40, textAlign: "center" }}>
          <p style={{ color: COLORS.textMuted, fontSize: 16, fontFamily: "system-ui, sans-serif", margin: 0 }}>
            Syntrix is working while you sleep.
          </p>
        </div>
      </div>

      {/* Right panel: Notification feed */}
      <div style={{ position: "absolute", right: 0, top: 0, width: "55%", height: "100%", overflow: "hidden" }}>
        <div style={{ padding: "60px 40px 0 40px" }}>
          <h3 style={{ color: COLORS.text, fontSize: 22, fontFamily: "system-ui, sans-serif", fontWeight: 600, marginBottom: 20 }}>
            Live Activity
          </h3>
        </div>
        {NOTIFICATIONS.map((n, i) => (
          <Notification
            key={i}
            text={n.text}
            icon={n.icon}
            color={n.color}
            delay={n.delay}
            y={i * 52}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
```

**Step 2: Wire into DemoVideo.tsx**

**Step 3: Verify** — notifications stack and accelerate.

**Step 4: Commit**

```bash
git add video/src/scenes/TheResults.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 5 — The Results with accelerating notification feed"
```

---

## Task 10: Scene 6 — Getting Rich

**Files:**
- Create: `video/src/scenes/GettingRich.tsx`
- Modify: `video/src/DemoVideo.tsx`

**Step 1: Create `video/src/scenes/GettingRich.tsx`**

```tsx
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS } from "../lib/colors";
import { Counter } from "../components/Counter";
import { MoneyRain } from "../components/MoneyRain";
import { HockeyStick } from "../components/HockeyStick";
import { ParticleBurst } from "../components/ParticleBurst";

export const GettingRich: React.FC = () => {
  const frame = useCurrentFrame();

  // Flash transition (first 10 frames)
  const flashOpacity = interpolate(frame, [0, 5, 10], [1, 0.8, 0], { extrapolateRight: "clamp" });

  // Background gold intensity builds
  const goldIntensity = interpolate(frame, [0, 250], [0.05, 0.3], { extrapolateRight: "clamp" });

  // Screen shake (increases over time)
  const shakeAmount = interpolate(frame, [100, 280], [0, 6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const shakeX = Math.sin(frame * 1.7) * shakeAmount;
  const shakeY = Math.cos(frame * 2.3) * shakeAmount;

  // Revenue counter uses exponential interpolation
  const revenueProgress = interpolate(frame, [30, 260], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const revenue = Math.pow(revenueProgress, 4) * 1_000_000;

  const formatRevenue = (n: number): string => {
    if (n >= 1_000_000) return "$1,000,000";
    if (n >= 100_000) return `$${(n / 1000).toFixed(0)}K`;
    if (n >= 1_000) return `$${(n / 1000).toFixed(1)}K`;
    return `$${Math.round(n)}`;
  };

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base }}>
      {/* Gold radial glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 50% 30%, ${COLORS.gold}${Math.round(goldIntensity * 255).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
        }}
      />

      {/* Shaking container */}
      <div style={{ transform: `translate(${shakeX}px, ${shakeY}px)`, width: "100%", height: "100%" }}>
        {/* Revenue counter */}
        <div style={{ position: "absolute", top: "15%", width: "100%", textAlign: "center" }}>
          <div style={{ color: COLORS.textMuted, fontSize: 18, fontFamily: "system-ui, sans-serif", marginBottom: 8 }}>
            Revenue
          </div>
          <div style={{ fontSize: 80, fontWeight: 800, fontFamily: "monospace", color: COLORS.goldBright }}>
            {formatRevenue(revenue)}
          </div>
        </div>

        {/* Hockey stick chart — centered below counter */}
        <div style={{ position: "absolute", top: "35%", left: "25%", width: "50%", height: "55%" }}>
          <HockeyStick startFrame={20} duration={240} />
        </div>
      </div>

      {/* Money rain */}
      <MoneyRain count={70} startFrame={15} />

      {/* Confetti bursts at milestones */}
      <ParticleBurst triggerFrame={120} count={60} color={COLORS.goldBright} radius={600} duration={45} />
      <ParticleBurst triggerFrame={200} count={80} color={COLORS.moneyGreen} radius={700} duration={50} />
      <ParticleBurst triggerFrame={260} count={100} color={COLORS.gold} radius={800} duration={40} />

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
```

**Step 2: Wire into DemoVideo.tsx**

**Step 3: Verify** — gold flash, revenue spinning, money rain, hockey stick chart, screen shake.

**Step 4: Commit**

```bash
git add video/src/scenes/GettingRich.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 6 — Getting Rich with money rain, hockey stick, and screen shake"
```

---

## Task 11: Scene 7 — CTA

**Files:**
- Create: `video/src/scenes/CTA.tsx`
- Modify: `video/src/DemoVideo.tsx`

**Step 1: Create `video/src/scenes/CTA.tsx`**

```tsx
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../lib/colors";
import { SPRING_SNAPPY } from "../lib/easing";

export const CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoSpring = spring({ fps, frame, config: SPRING_SNAPPY });
  const logoScale = interpolate(logoSpring, [0, 1], [0.5, 1]);
  const logoOpacity = interpolate(logoSpring, [0, 0.3], [0, 1], { extrapolateRight: "clamp" });

  const line1Opacity = interpolate(frame, [15, 25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const line2Opacity = interpolate(frame, [25, 35], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const line3Opacity = interpolate(frame, [35, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.base, justifyContent: "center", alignItems: "center" }}>
      {/* Logo */}
      <div style={{ transform: `scale(${logoScale})`, opacity: logoOpacity, textAlign: "center", marginBottom: 40 }}>
        <h1
          style={{
            fontSize: 72,
            fontWeight: 800,
            fontFamily: "system-ui, sans-serif",
            background: `linear-gradient(135deg, ${COLORS.cyan}, ${COLORS.magenta})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            margin: 0,
          }}
        >
          Syntrix
        </h1>
      </div>

      {/* CTA lines */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
        <div style={{ opacity: line1Opacity }}>
          <code
            style={{
              fontSize: 20,
              color: COLORS.green,
              fontFamily: "monospace",
              padding: "8px 20px",
              borderRadius: 8,
              backgroundColor: `${COLORS.green}11`,
              border: `1px solid ${COLORS.green}33`,
            }}
          >
            docker compose up
          </code>
        </div>
        <div style={{ opacity: line2Opacity }}>
          <span style={{ fontSize: 22, color: COLORS.cyan, fontFamily: "system-ui, sans-serif" }}>
            syntrix.app
          </span>
        </div>
        <div style={{ opacity: line3Opacity, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 18, color: COLORS.textMuted, fontFamily: "system-ui, sans-serif" }}>
            ⭐ Star on GitHub
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

**Step 2: Wire into DemoVideo.tsx — replace all 7 placeholder scenes with real imports.**

**Step 3: Verify full 60s video plays through all scenes.**

**Step 4: Commit**

```bash
git add video/src/scenes/CTA.tsx video/src/DemoVideo.tsx
git commit -m "feat(video): Scene 7 — CTA with docker compose, syntrix.app, and GitHub star"
```

---

## Task 12: Wire Final DemoVideo.tsx with All Scenes

**Files:**
- Modify: `video/src/DemoVideo.tsx` — import all real scene components

**Step 1: Update DemoVideo.tsx**

Replace all placeholder `<AbsoluteFill>` blocks with the real scene components:

```tsx
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
```

**Step 2: Run full preview**

Run: `cd video && npm run studio`
Expected: Full 60-second video plays through all 7 scenes with smooth transitions.

**Step 3: Render MP4**

Run: `cd video && npm run render`
Expected: `video/out/demo-1080p.mp4` generated (1920x1080, 60s, ~30fps).

**Step 4: Commit**

```bash
git add video/src/DemoVideo.tsx
git commit -m "feat(video): wire all 7 scenes into DemoVideo composition"
```

---

## Task 13: Landing Page Integration — DemoEmbed Component

**Files:**
- Create: `landing/src/components/DemoEmbed.tsx`
- Modify: `landing/src/app/page.tsx:1-25` — add DemoEmbed between Hero and TrustBar
- Modify: `landing/package.json` — add `@remotion/player` dependency

**Step 1: Install @remotion/player in landing**

Run:
```bash
cd landing && npm install --save-exact @remotion/player@4.0.399 remotion@4.0.399
```

**Step 2: Create `landing/src/components/DemoEmbed.tsx`**

Since the video/ project is standalone, the simplest embed approach for the landing page is to use a `<video>` tag with the pre-rendered MP4 (hosted or in `public/`). This avoids cross-project dependency issues. We can upgrade to `@remotion/player` live rendering later if needed.

```tsx
"use client";

import { useEffect, useRef, useState } from "react";

export function DemoEmbed() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const sectionRef = useRef<HTMLElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Auto-play when in viewport
  useEffect(() => {
    const video = videoRef.current;
    const section = sectionRef.current;
    if (!video || !section) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isPlaying) {
          video.play().catch(() => {});
          setIsPlaying(true);
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(section);
    return () => observer.disconnect();
  }, [isPlaying]);

  return (
    <section ref={sectionRef} className="bg-base py-20">
      <div className="mx-auto max-w-5xl px-6">
        {/* Heading */}
        <div className="mb-10 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            See how Syntrix turns tweets into{" "}
            <span className="bg-gradient-to-r from-cyan-400 to-fuchsia-500 bg-clip-text text-transparent">
              customers
            </span>
          </h2>
          <p className="mt-3 font-body text-lg text-slate-400">
            60 seconds. Zero fluff.
          </p>
        </div>

        {/* Video player */}
        <div className="relative overflow-hidden rounded-2xl border border-white/10 shadow-2xl shadow-cyan-500/10">
          <video
            ref={videoRef}
            src="/demo.mp4"
            muted
            playsInline
            loop
            className="w-full"
            poster="/demo-poster.jpg"
          />
        </div>

        {/* CTA row below video */}
        <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="https://github.com/StrangeStorm243-bit/Syntrix"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-6 py-3 font-mono text-sm text-white transition-colors hover:bg-white/10"
          >
            ⭐ Star on GitHub
          </a>
          <a
            href="#quickstart"
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-3 font-mono text-sm text-white transition-opacity hover:opacity-90"
          >
            Get Started →
          </a>
        </div>
      </div>
    </section>
  );
}
```

**Step 3: Update `landing/src/app/page.tsx`**

Add the import and place `<DemoEmbed />` between `<Hero />` and `<TrustBar />`:

```tsx
import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { DemoEmbed } from "@/components/DemoEmbed";
import { TrustBar } from "@/components/TrustBar";
import { Pipeline } from "@/components/Pipeline";
import { Features } from "@/components/Features";
import { TerminalShowcase } from "@/components/TerminalShowcase";
import { QuickStart } from "@/components/QuickStart";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="bg-base">
        <Hero />
        <DemoEmbed />
        <TrustBar />
        <Pipeline />
        <Features />
        <TerminalShowcase />
        <QuickStart />
      </main>
      <Footer />
    </>
  );
}
```

**Step 4: Verify landing page builds**

Run:
```bash
cd landing && npm run build
```

Expected: Build succeeds. The video player section renders (video file will be missing until we copy the rendered MP4 to `landing/public/demo.mp4`).

**Step 5: Commit**

```bash
git add landing/src/components/DemoEmbed.tsx landing/src/app/page.tsx landing/package.json landing/package-lock.json
git commit -m "feat(landing): add DemoEmbed section with video player and CTA between Hero and TrustBar"
```

---

## Task 14: Copy Rendered Video to Landing + End-to-End Verification

**Files:**
- Copy: `video/out/demo-1080p.mp4` → `landing/public/demo.mp4`
- Create: `video/.gitignore`

**Step 1: Create `video/.gitignore`**

```
node_modules/
out/
dist/
```

**Step 2: Render final video**

Run:
```bash
cd video && npm run render
```

**Step 3: Copy to landing**

Run:
```bash
cp video/out/demo-1080p.mp4 landing/public/demo.mp4
```

**Step 4: Generate poster frame (first frame screenshot)**

Run:
```bash
cd video && npx remotion still src/index.ts DemoVideo landing/../landing/public/demo-poster.jpg --frame=240
```

(Frame 240 = start of Scene 2 "Enter Syntrix" — a nice poster image.)

**Step 5: Run landing dev server and verify**

Run:
```bash
cd landing && npm run dev
```

Expected: Visit `http://localhost:3000`. Below the hero section, the demo video section appears with:
- "See how Syntrix turns tweets into customers" heading
- Video player that auto-plays on scroll
- Star on GitHub + Get Started CTAs below

**Step 6: Commit**

```bash
git add video/.gitignore landing/public/demo.mp4 landing/public/demo-poster.jpg
git commit -m "feat: add rendered demo video and poster to landing page"
```

**Step 7: Push branch**

```bash
git push -u origin feat/remotion-demo-video
```

---

## Summary of All Tasks

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | Scaffold Remotion project | `video/package.json`, `Root.tsx`, `DemoVideo.tsx`, `lib/` |
| 2 | TweetBubble + Typewriter components | `video/src/components/` |
| 3 | Counter + Scanlines + ParticleBurst | `video/src/components/` |
| 4 | Notification + PipelineStage + MoneyRain + HockeyStick | `video/src/components/` |
| 5 | Scene 1 — The Problem | `video/src/scenes/TheProblem.tsx` |
| 6 | Scene 2 — Enter Syntrix | `video/src/scenes/EnterSyntrix.tsx` |
| 7 | Scene 3 — The Pipeline | `video/src/scenes/ThePipeline.tsx` |
| 8 | Scene 4 — The Dashboard | `video/src/scenes/TheDashboard.tsx` |
| 9 | Scene 5 — The Results | `video/src/scenes/TheResults.tsx` |
| 10 | Scene 6 — Getting Rich | `video/src/scenes/GettingRich.tsx` |
| 11 | Scene 7 — CTA | `video/src/scenes/CTA.tsx` |
| 12 | Wire all scenes into DemoVideo | `video/src/DemoVideo.tsx` |
| 13 | Landing page DemoEmbed component | `landing/src/components/DemoEmbed.tsx`, `page.tsx` |
| 14 | Render video + copy to landing + verify | `landing/public/demo.mp4` |
