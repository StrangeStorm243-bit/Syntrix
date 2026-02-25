# Architecture Research

**Domain:** Cyberpunk immersive 3D dashboard — progressive upgrade of existing React 19 SPA
**Researched:** 2026-02-24
**Confidence:** HIGH

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │  Pages   │  │  3D      │  │ Pipeline │  │ Ambient / Effects    │ │
│  │ (exist.) │  │  Scenes  │  │ DAG View │  │ (particles, bloom,   │ │
│  │          │  │  (R3F)   │  │ (xyflow) │  │  scanlines, glitch)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
│       │             │             │                    │             │
├───────┴─────────────┴─────────────┴────────────────────┴─────────────┤
│                      Component + Animation Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │ shadcn/  │  │ Motion   │  │ Magic/   │  │ augmented-ui         │ │
│  │ ui base  │  │ v12      │  │ Acet.    │  │ + CYBERCORE CSS      │ │
│  │ comps    │  │ anims    │  │ cherry-  │  │ HUD borders          │ │
│  │          │  │          │  │ picks    │  │                      │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
│       │             │             │                    │             │
├───────┴─────────────┴─────────────┴────────────────────┴─────────────┤
│                        Design System Layer                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  CSS Variables (cyberpunk palette) + Tailwind 4 Theme Extension │ │
│  │  + cn() utility + shared animation presets + glassmorphism      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│                          Data Layer (unchanged)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                           │
│  │ TanStack │  │ WebSocket│  │ API      │                           │
│  │ Query    │  │ Client   │  │ Client   │                           │
│  └──────────┘  └──────────┘  └──────────┘                           │
└──────────────────────────────────────────────────────────────────────┘
```

### Layer Boundaries

The architecture has four clean layers. The critical principle: **3D and effects are presentation concerns only — they never own data.** Data always flows up from the existing Data Layer through hooks, and the 3D/animation layers subscribe to that data reactively.

| Layer | Owns | Does NOT Own |
|-------|------|-------------|
| Presentation | Visual rendering, scene composition, route pages | Data fetching, business logic, API shape |
| Component + Animation | Reusable UI primitives, motion presets, transitions | Page layout, data flow, 3D scene logic |
| Design System | Color tokens, spacing, typography, glass/neon utilities | Component behavior, state, animations |
| Data | API calls, caching, WebSocket, server state | Rendering, styling, animation |

## Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| `CyberpunkLayout` | Root layout wrapper — sidebar, ambient particles, global effects, page transition container | Pages (via `<Outlet />`), Design System (CSS vars), `ParticleBackground` |
| `ParticleBackground` | Ambient floating particle canvas behind all pages — tsParticles engine | `CyberpunkLayout` (parent mount point) |
| `NeonSidebar` | Cyberpunk-styled nav with glow active states, scanline overlay | `CyberpunkLayout`, Router (NavLink) |
| `GlassCard` | Base card primitive — glassmorphism background, augmented-ui borders, neon glow | All pages (used everywhere cards appear) |
| `NeonMetricCard` | Animated metric card — number counter, glow pulse on change, neon border | `Dashboard` page, TanStack Query data hooks |
| `CyberChart` | Recharts wrapper — neon gradients, glassmorphism tooltip, warm color scheme | Analytics page, Dashboard page, TanStack Query |
| `PipelineScene` | R3F Canvas — 3D particle flow between pipeline stage nodes | `PipelineLiveView` page wrapper, WebSocket data |
| `PipelineDAG` | @xyflow/react DAG — 2D fallback / alternative pipeline view with elkjs layout | `PipelineLiveView` page, WebSocket data, useStats hook |
| `StageNode` | Custom xyflow node — cyberpunk styled pipeline stage (collect, judge, score, draft, send) | `PipelineDAG` (registered as custom nodeType) |
| `DataStream` | Animated particle edge in xyflow or R3F — shows data flowing between stages | `PipelineDAG` or `PipelineScene` |
| `HeroScene` | R3F Canvas — dashboard overview 3D background (abstract geometry, bloom) | `Dashboard` page (positioned behind metric grid) |
| `PageTransition` | AnimatePresence + motion.div wrapper for route-level enter/exit animations | `CyberpunkLayout` (wraps `<Outlet />`) |

## Recommended Project Structure

```
dashboard/src/
├── components/                  # Existing components (preserved)
│   ├── DataTable.tsx            # [existing] — will get cyberpunk styling pass
│   ├── DraftCard.tsx            # [existing] — will get GlassCard wrapper
│   ├── MetricCard.tsx           # [existing] — preserved, new NeonMetricCard replaces usage
│   ├── Sidebar.tsx              # [existing] — preserved, new NeonSidebar replaces usage
│   ├── TopBar.tsx               # [existing] — preserved
│   ├── ...                      # other existing components unchanged
│   └── __tests__/               # existing test files relocated (or colocated)
│
├── components/cyber/            # NEW — cyberpunk design system components
│   ├── GlassCard.tsx            # Glassmorphism card with augmented-ui border
│   ├── NeonMetricCard.tsx       # Animated metric card with counter + glow
│   ├── NeonSidebar.tsx          # Cyberpunk sidebar with scanline + glow nav
│   ├── NeonBadge.tsx            # Score/judgment badges with neon coloring
│   ├── NeonButton.tsx           # Button with glow hover, click ripple
│   ├── NeonTable.tsx            # Data table with row hover glow, header scanline
│   ├── NeonInput.tsx            # Input/select with neon focus ring
│   ├── NeonTooltip.tsx          # Glassmorphism tooltip for Recharts
│   └── PageTransition.tsx       # AnimatePresence route wrapper
│
├── components/charts/           # NEW — cyberpunk Recharts wrappers
│   ├── CyberBarChart.tsx        # Bar chart with neon gradient fills
│   ├── CyberFunnelChart.tsx     # Funnel with warm gradient + glow
│   └── chart-theme.ts           # Shared Recharts color/style tokens
│
├── scenes/                      # NEW — React Three Fiber 3D scenes
│   ├── HeroScene.tsx            # Dashboard background (abstract geometry + bloom)
│   ├── PipelineScene.tsx        # 3D pipeline particle flow
│   ├── PipelineParticles.tsx    # Particle system for data flow visualization
│   ├── StageOrb.tsx             # Glowing orb representing a pipeline stage
│   ├── effects.tsx              # EffectComposer setup (Bloom, ChromaticAberration)
│   └── scene-utils.ts           # Shared 3D helpers (colors, materials, geometries)
│
├── pipeline/                    # NEW — @xyflow/react pipeline DAG components
│   ├── PipelineDAG.tsx          # ReactFlow + elkjs layout orchestrator
│   ├── StageNode.tsx            # Custom node — cyberpunk pipeline stage
│   ├── DataEdge.tsx             # Custom animated edge — particle/pulse flow
│   ├── pipeline-layout.ts       # elkjs config and layout computation
│   └── pipeline-types.ts        # Shared types for DAG nodes/edges
│
├── effects/                     # NEW — ambient visual effects
│   ├── ParticleBackground.tsx   # tsParticles ambient floating particles
│   ├── Scanlines.tsx            # CSS scanline overlay component
│   ├── GlitchText.tsx           # CYBERCORE glitch text effect
│   └── NeonGlow.tsx             # Reusable neon glow CSS utility component
│
├── hooks/                       # Existing hooks (preserved + extended)
│   ├── useAnalytics.ts          # [existing] — unchanged
│   ├── useLeads.ts              # [existing] — unchanged
│   ├── useQueue.ts              # [existing] — unchanged
│   ├── useStats.ts              # [existing] — unchanged
│   ├── useExperiments.ts        # [existing] — unchanged
│   ├── useWebSocket.ts          # [existing] — unchanged
│   ├── usePipelineFlow.ts       # NEW — transforms WS + stats data into DAG nodes/edges
│   ├── useReducedMotion.ts      # NEW — respects prefers-reduced-motion
│   └── useGPUTier.ts            # NEW — detect-gpu for adaptive quality
│
├── layouts/
│   ├── DashboardLayout.tsx      # [existing] — preserved as-is
│   └── CyberpunkLayout.tsx      # NEW — replaces DashboardLayout in route tree
│
├── pages/                       # Existing pages (preserved, progressively upgraded)
│   ├── Dashboard.tsx            # [existing] — wrap with HeroScene background
│   ├── Leads.tsx                # [existing] — swap to NeonTable
│   ├── Queue.tsx                # [existing] — wrap DraftCards in GlassCard
│   ├── Analytics.tsx            # [existing] — swap to CyberChart wrappers
│   ├── Experiments.tsx          # [existing] — swap to NeonTable
│   ├── Settings.tsx             # [existing] — NeonInput styling pass
│   └── PipelineLive.tsx         # NEW — the hero page, 3D pipeline live view
│
├── lib/                         # Existing lib (preserved + extended)
│   ├── api.ts                   # [existing] — unchanged
│   ├── utils.ts                 # [existing] — unchanged
│   ├── websocket.ts             # [existing] — unchanged
│   └── animation-presets.ts     # NEW — shared Motion v12 animation configs
│
├── styles/                      # NEW — cyberpunk design tokens
│   ├── cyberpunk-vars.css       # CSS custom properties (palette, spacing, glow)
│   ├── augmented-ui.css         # augmented-ui imports + custom clip-paths
│   ├── scanlines.css            # Scanline overlay keyframes
│   └── glassmorphism.css        # Glass effect utility classes
│
├── App.tsx                      # [existing] — swap DashboardLayout -> CyberpunkLayout
├── index.css                    # [existing] — add @import for cyberpunk-vars.css
└── main.tsx                     # [existing] — unchanged
```

### Structure Rationale

- **`components/cyber/`**: Isolates cyberpunk components from existing ones. During the progressive upgrade, pages import from `cyber/` instead of the old component. The old components remain importable as fallback. Once upgrade is complete across all pages, old components can be removed or aliased.

- **`scenes/`**: All React Three Fiber code lives here. This directory is the only place that imports from `@react-three/fiber`, `drei`, or `postprocessing`. This boundary is critical because Three.js is the heaviest dependency (~600KB) and must be lazy-loaded. Keeping it isolated means tree-shaking and code-splitting work cleanly.

- **`pipeline/`**: All @xyflow/react code lives here. Separate from `scenes/` because the DAG view is a 2D React component (HTML/SVG), not a WebGL canvas. It has its own dependency tree (elkjs, @xyflow/react) that should also be code-split.

- **`effects/`**: Lightweight CSS/canvas effects that do not require Three.js. tsParticles, scanlines, and glitch effects are cheaper than R3F and can load eagerly or with minimal delay.

- **`styles/`**: CSS-only design tokens. No JS, no component logic. Imported globally via `index.css`. This is what makes the cyberpunk theme pervasive without touching component code — every existing Tailwind class picks up the new palette through CSS variable remapping.

## Data Flow

### Primary Data Flow (unchanged from existing architecture)

```
FastAPI Backend (port 8400)
        │
        ├── REST API (/api/*)
        │       │
        │   apiGet / apiPost (lib/api.ts)
        │       │
        │   TanStack Query hooks (hooks/use*.ts)
        │       │
        │   React components (pages + components)
        │
        └── WebSocket (/ws/pipeline)
                │
            SignalOpsWebSocket (lib/websocket.ts)
                │
            useWebSocket hook
                │
            Components that need real-time data
```

### 3D Scene Data Flow (new layer)

```
useStats() ──────────────────┐
useWebSocket() ──────────────┤
                             ▼
                    usePipelineFlow()
                    (transforms data into DAG shape)
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        PipelineDAG    PipelineScene    NeonMetricCard
        (@xyflow)      (R3F Canvas)    (animated counters)
              │              │
         StageNode      StageOrb
         DataEdge       PipelineParticles
```

The critical connector is `usePipelineFlow()` — a custom hook that:
1. Subscribes to `useStats()` for aggregate counts per stage
2. Subscribes to `useWebSocket()` for real-time `pipeline_progress` events
3. Outputs a normalized data structure consumed by both the 2D DAG and 3D scene:

```typescript
interface PipelineFlowData {
  stages: {
    id: string;            // "collect" | "judge" | "score" | "draft" | "send"
    label: string;
    count: number;         // items processed
    active: boolean;       // currently processing
    progress: number;      // 0-100 for current batch
  }[];
  connections: {
    from: string;
    to: string;
    throughput: number;    // items/minute flowing through
  }[];
  recentEvents: {
    stage: string;
    detail: string;
    timestamp: number;
  }[];
}
```

### Chart Data Flow (new wrapper layer)

```
useScoreDistribution() ──┐
useConversionFunnel() ────┤
useQueryPerformance() ────┘
                          │
                     Existing hooks return raw data
                          │
                     CyberBarChart / CyberFunnelChart
                     (Recharts + cyberpunk theme tokens)
                          │
                     chart-theme.ts provides:
                       - neonGradients (SVG <defs>)
                       - tooltipStyle (glassmorphism)
                       - axisStyle (warm gray + neon)
                       - barRadius, fillColors
```

Chart wrappers do NOT add a new data layer — they accept the same data shapes as the existing Recharts components but apply the cyberpunk theme. This is a pure presentation concern.

### Animation Data Flow

```
Page mount/unmount ────> AnimatePresence (PageTransition)
                               │
                          motion.div with enter/exit variants
                               │
                          animation-presets.ts provides:
                            - pageEnter: { opacity, y, filter }
                            - pageExit: { opacity, y, filter }
                            - stagger children config
                            - spring physics constants

User interaction ────> motion.div (GlassCard hover)
                            │
                       whileHover / whileTap variants
                            │
                       CSS transition for glow intensity
                       (cheaper than JS animation)
```

Animation orchestration rule: **CSS transitions for simple hover/focus effects. Motion v12 for enter/exit/layout. R3F useFrame for continuous 3D animation.** Never mix — each tool owns its domain.

## Architectural Patterns

### Pattern 1: Lazy-Loaded 3D Boundary

**What:** All R3F Canvas components are wrapped in `React.lazy()` + `<Suspense>` with a non-3D fallback. The Three.js bundle (~600KB) never loads until the user navigates to a page that needs it.

**When to use:** Every R3F scene mount point.

**Trade-offs:** First load of a 3D page has a brief fallback flash. Acceptable because the fallback itself is styled (a pulsing neon skeleton). Prevents 600KB penalty on initial dashboard load.

**Example:**
```typescript
// pages/Dashboard.tsx
import { Suspense, lazy } from 'react';

const HeroScene = lazy(() => import('../scenes/HeroScene'));

export default function Dashboard() {
  const { data: stats } = useStats();

  return (
    <div className="relative">
      {/* 3D background — lazy, behind content */}
      <div className="absolute inset-0 -z-10">
        <Suspense fallback={<div className="h-full w-full bg-void" />}>
          <HeroScene stats={stats} />
        </Suspense>
      </div>

      {/* Regular 2D content — loads immediately */}
      <div className="relative z-10 space-y-6">
        <NeonMetricCard label="Total Leads" value={stats?.scored ?? 0} />
        {/* ... */}
      </div>
    </div>
  );
}
```

### Pattern 2: Adapter Hook Between Data and Visualization

**What:** A custom hook transforms raw API/WebSocket data into the shape needed by visualization components. The visualization never calls API hooks directly.

**When to use:** Pipeline DAG, Pipeline 3D scene, any component that combines multiple data sources.

**Trade-offs:** One more abstraction layer. Worth it because it decouples the visualization from the API shape, making both independently testable. If the API changes, only the adapter hook changes.

**Example:**
```typescript
// hooks/usePipelineFlow.ts
export function usePipelineFlow(): PipelineFlowData {
  const { data: stats } = useStats();
  const { lastMessage } = useWebSocket();
  const [recentEvents, setRecentEvents] = useState<PipelineEvent[]>([]);

  useEffect(() => {
    if (lastMessage?.type === 'pipeline_progress') {
      setRecentEvents(prev => [
        { stage: lastMessage.stage, detail: lastMessage.detail, timestamp: Date.now() },
        ...prev.slice(0, 49),  // keep last 50
      ]);
    }
  }, [lastMessage]);

  return useMemo(() => ({
    stages: PIPELINE_STAGES.map(s => ({
      id: s.id,
      label: s.label,
      count: stats?.[s.statsKey] ?? 0,
      active: recentEvents.some(e => e.stage === s.id && Date.now() - e.timestamp < 5000),
      progress: lastMessage?.stage === s.id ? lastMessage.progress : 0,
    })),
    connections: PIPELINE_CONNECTIONS.map(c => ({
      ...c,
      throughput: computeThroughput(stats, c),
    })),
    recentEvents,
  }), [stats, recentEvents, lastMessage]);
}
```

### Pattern 3: Progressive Component Swap

**What:** Pages import new cyberpunk components alongside old ones during the upgrade. A feature flag or simple swap controls which renders. Once validated, old imports are removed.

**When to use:** Every page during the upgrade process.

**Trade-offs:** Temporarily larger imports during upgrade. This is the progressive guarantee — at no point does a page fully break because the old component is still there as fallback.

**Example:**
```typescript
// During upgrade: Dashboard.tsx
import { MetricCard } from '../components/MetricCard';           // old
import { NeonMetricCard } from '../components/cyber/NeonMetricCard'; // new

// Swap is a simple replacement: MetricCard -> NeonMetricCard
// Same props interface, different presentation
<NeonMetricCard label="Total Leads" value={stats?.scored ?? 0} icon={<Users size={18} />} />
```

### Pattern 4: Adaptive Quality with GPU Detection

**What:** Use `detect-gpu` (or a simple WebGL capability check) at app init to set a quality tier. 3D scenes read this tier and adjust: HIGH = full postprocessing + particles, MEDIUM = no postprocessing, LOW = static 2D fallback.

**When to use:** Every R3F scene and ParticleBackground.

**Trade-offs:** Complexity in maintaining multiple render paths. Essential because cyberpunk effects are GPU-intensive — without this, low-end machines get slideshow frame rates.

**Example:**
```typescript
// hooks/useGPUTier.ts
type GPUTier = 'high' | 'medium' | 'low';

export function useGPUTier(): GPUTier {
  const [tier, setTier] = useState<GPUTier>('medium');

  useEffect(() => {
    // Check WebGL2 support + rough GPU capability
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2');
    if (!gl) { setTier('low'); return; }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : '';

    // Simple heuristic: integrated GPUs get medium, dedicated get high
    if (/Intel|Mali|Adreno/i.test(renderer)) setTier('medium');
    else setTier('high');
  }, []);

  return tier;
}

// scenes/HeroScene.tsx
function HeroScene({ stats }: Props) {
  const tier = useGPUTier();

  if (tier === 'low') return <StaticHeroFallback />;

  return (
    <Canvas>
      <HeroGeometry stats={stats} />
      {tier === 'high' && (
        <EffectComposer>
          <Bloom luminanceThreshold={0.6} intensity={1.5} />
          <ChromaticAberration offset={[0.001, 0.001]} />
        </EffectComposer>
      )}
    </Canvas>
  );
}
```

## Build Order (Dependency Graph)

The build order is driven by dependencies — each phase produces artifacts consumed by later phases. Within a phase, items can be built in parallel.

### Phase 0: Foundation (no visual changes, enables everything)

```
cyberpunk-vars.css ────> index.css imports it
         │
cn() utility preserved (already exists)
         │
CyberpunkLayout.tsx ──> wraps existing Outlet, adds CSS class scope
         │
App.tsx route swap: DashboardLayout -> CyberpunkLayout
```

**Produces:** Cyberpunk color tokens available globally. All existing pages render identically inside the new layout (visual parity checkpoint).

**Build order rationale:** CSS variables must exist before any cyberpunk component references them. The layout swap must be non-breaking — `CyberpunkLayout` initially renders identically to `DashboardLayout` but with the cyberpunk class scope applied.

### Phase 1: Design System Components (parallel builds)

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ GlassCard.tsx   │  │ NeonSidebar.tsx  │  │ PageTransition  │
│ NeonButton.tsx  │  │ NeonBadge.tsx    │  │ (Motion v12)    │
│ NeonInput.tsx   │  │ NeonTable.tsx    │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                    All depend on: Phase 0 (CSS vars)
                    All independent of each other
```

**Produces:** Reusable cyberpunk primitives. No page changes yet — components exist but are not imported by any page.

### Phase 2: Ambient Effects Layer

```
ParticleBackground.tsx ──> mounted in CyberpunkLayout
Scanlines.tsx ─────────> optional overlay in CyberpunkLayout
animation-presets.ts ──> shared Motion configs
useReducedMotion.ts ───> accessibility gate
```

**Produces:** The "feel" of cyberpunk — particles floating, subtle scanlines, page transitions active. All existing page content still renders through old components.

**Depends on:** Phase 0 (layout mount point), Phase 1 (PageTransition used in layout)

### Phase 3: Page Upgrades — Dashboard + Analytics (parallel)

```
┌─────────────────────┐  ┌─────────────────────────┐
│ NeonMetricCard swap  │  │ CyberBarChart.tsx        │
│ in Dashboard.tsx     │  │ CyberFunnelChart.tsx     │
│                      │  │ chart-theme.ts           │
│                      │  │ Analytics.tsx swap        │
└──────────┬───────────┘  └──────────┬──────────────┘
           │                         │
           └────────┬────────────────┘
                    │
          Depend on: Phase 1 (GlassCard, NeonBadge)
```

**Produces:** Two pages fully cyberpunk-styled. First visual wow moment.

### Phase 4: Pipeline Visualization (the hero feature)

```
pipeline-types.ts ──────────────┐
pipeline-layout.ts (elkjs) ─────┤
                                ▼
usePipelineFlow.ts ────> StageNode.tsx ────> PipelineDAG.tsx
                    │                              │
                    │    DataEdge.tsx ──────────────┘
                    │
                    └──> PipelineScene.tsx (R3F)
                              │
                         StageOrb.tsx
                         PipelineParticles.tsx
                         effects.tsx (Bloom)
                              │
                         PipelineLive.tsx (page)
```

**Depends on:** Phase 0 (CSS vars), Phase 1 (GlassCard for node styling), Phase 2 (animation presets). Does NOT depend on Phase 3.

**Build order within Phase 4:**
1. `pipeline-types.ts` + `usePipelineFlow.ts` (data layer first, testable without UI)
2. `pipeline-layout.ts` + `StageNode.tsx` + `DataEdge.tsx` (2D DAG components)
3. `PipelineDAG.tsx` (assembles 2D view — milestone: working 2D pipeline)
4. `StageOrb.tsx` + `PipelineParticles.tsx` + `effects.tsx` (3D components)
5. `PipelineScene.tsx` (assembles 3D view — milestone: working 3D pipeline)
6. `PipelineLive.tsx` (page: toggle between 2D/3D, route integration)

**Produces:** The core value proposition — animated pipeline visualization.

### Phase 5: Dashboard Hero 3D Scene

```
HeroScene.tsx ──> scene-utils.ts
      │
      └──> useGPUTier.ts
      │
Dashboard.tsx ──> lazy-loads HeroScene as background
```

**Depends on:** Phase 3 (Dashboard already has NeonMetricCards), Phase 4 patterns (R3F experience established).

**Produces:** Dashboard overview has a living 3D background behind the metric grid.

### Phase 6: Remaining Page Upgrades (parallel)

```
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Leads.tsx     │  │ Queue.tsx     │  │ Experiments   │  │ Settings.tsx  │
│ NeonTable     │  │ GlassCard     │  │ .tsx          │  │ NeonInput     │
│ NeonBadge     │  │ wrap          │  │ NeonTable     │  │ NeonButton    │
└───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
         │                │                  │                  │
         └────────────────┴──────────────────┴──────────────────┘
                                    │
                          Depend on: Phase 1 (components exist)
                          Independent of Phase 4/5 (can run in parallel)
```

**Produces:** All 6 pages fully cyberpunk-styled. Complete visual coherence.

### Phase 7: Polish + Performance

```
useReducedMotion ──> gate all Motion animations
useGPUTier ────────> gate all R3F scenes
Lighthouse audit ──> optimize bundle splits
                     verify lazy-load boundaries
                     test on integrated GPU hardware
```

### Build Dependency Summary

```
Phase 0 (Foundation)
  ├── Phase 1 (Design System) ──> Phase 3 (Dashboard + Analytics upgrade)
  │                                        │
  ├── Phase 2 (Ambient Effects) ───────────┤
  │                                        ▼
  │                                Phase 5 (Hero 3D Scene)
  │
  ├── Phase 4 (Pipeline Viz) ──────────────> standalone, can parallelize with Phase 3
  │
  └── Phase 6 (Remaining Pages) ───────────> depends only on Phase 1
                                                 can parallelize with Phase 4/5
Phase 7 (Polish) ── depends on all above
```

## Anti-Patterns

### Anti-Pattern 1: 3D Components That Fetch Data

**What people do:** Put `useQuery` or `useWebSocket` calls inside R3F scene components (components rendered inside `<Canvas>`).

**Why it's wrong:** R3F components run inside a different React reconciler. While hooks technically work, mixing data concerns with render-loop concerns creates debugging nightmares and makes components impossible to test without a full R3F context. Also, if the data fetch triggers a re-render, it can cause the entire 3D scene to re-mount.

**Do this instead:** Pass data as props to scene components. The parent page component (outside `<Canvas>`) owns the hooks and passes data down. Use `useMemo` to prevent unnecessary scene re-renders.

### Anti-Pattern 2: Animating Everything with the Same Tool

**What people do:** Use Motion v12 for hover effects that CSS transitions handle fine, or use CSS transitions for layout animations that need AnimatePresence.

**Why it's wrong:** Motion v12 adds JS overhead for every animated element. Using it for simple `opacity` or `background-color` hover transitions wastes bundle and runtime. Conversely, CSS cannot handle exit animations or layout animations.

**Do this instead:** Follow the tool hierarchy:
1. CSS `transition` — hover, focus, color changes, simple transforms
2. Motion v12 — enter/exit, layout shifts, scroll-linked, gesture-driven
3. R3F `useFrame` — continuous 3D animation loops
4. GSAP — complex multi-element sequenced timelines (rare, avoid if possible)

### Anti-Pattern 3: Global Canvas for Everything

**What people do:** Create a single full-screen R3F `<Canvas>` and render all 3D content (hero scene, pipeline, particles) in one scene.

**Why it's wrong:** WebGL contexts are expensive. A single always-on canvas prevents code-splitting scenes, makes page transitions impossible (the canvas persists across routes), and complicates state management. Also, the canvas intercepts all pointer events by default.

**Do this instead:** Each page that needs 3D gets its own lazy-loaded `<Canvas>` instance. When the user navigates away, the canvas unmounts and the WebGL context is released. This aligns with React's component model and enables route-level code splitting.

### Anti-Pattern 4: Tight Coupling Between 2D DAG and 3D Scene

**What people do:** Build the pipeline visualization so the 2D @xyflow view and 3D R3F view share internal state or components.

**Why it's wrong:** @xyflow is an HTML/SVG renderer. R3F is a WebGL renderer. They cannot share components. Attempting to create "universal" pipeline nodes that work in both contexts leads to abstraction layers that fit neither well.

**Do this instead:** Both views consume the same data hook (`usePipelineFlow`) but render completely independently. `PipelineDAG` uses `StageNode` (HTML). `PipelineScene` uses `StageOrb` (Three.js mesh). The shared contract is the data shape, not the components.

### Anti-Pattern 5: Blocking Initial Load with Heavy Dependencies

**What people do:** Import Three.js, @xyflow/react, tsParticles, augmented-ui, and GSAP in the main bundle.

**Why it's wrong:** Three.js alone is ~600KB. @xyflow is ~150KB. Loading all of this before the first paint means a 3-5 second white screen on average connections. The existing dashboard loads in under 1 second — this must be preserved.

**Do this instead:** The only eagerly-loaded additions are: CSS files (cyberpunk-vars, augmented-ui, scanlines — all < 10KB total) and the Phase 1 design system components (lightweight, no heavy deps). Everything else is `React.lazy()` with route-level code splitting. tsParticles loads after first paint via `useEffect`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| FastAPI backend (REST) | Existing `apiGet`/`apiPost` via TanStack Query — unchanged | No new endpoints needed |
| FastAPI backend (WS) | Existing `SignalOpsWebSocket` class — unchanged | `pipeline_progress` events drive both DAG and 3D scene |
| Three.js CDN assets | None — all geometry is procedural, no external model files | Keeps bundle self-contained, no CORS or loading issues |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Pages <-> 3D Scenes | Props down (data), never events up | Scene components are pure renderers |
| Pages <-> DAG | Props down (nodes/edges), callbacks up (node click) | Node click may open a detail panel — standard React callback |
| CyberpunkLayout <-> Pages | CSS class scope + `<Outlet />` | Layout provides ambient effects, pages provide content |
| Design System <-> All Components | CSS variables consumed via Tailwind classes | No JS coupling — `var(--neon-primary)` is the interface |
| Motion v12 <-> R3F | No direct interaction | They animate different DOM trees (HTML vs Canvas) |
| usePipelineFlow <-> useStats + useWebSocket | Hook composition | `usePipelineFlow` calls the other hooks internally |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (1 user, dev mode) | No issues. All effects run fine. Vite dev server handles HMR for all file types including 3D scenes. |
| 10-50 concurrent users | No change needed. Each browser instance runs its own R3F and WebSocket. Backend unchanged. |
| Low-end hardware | `useGPUTier` detects and degrades: no postprocessing, fewer particles, 2D fallback for scenes. Test on Intel integrated GPU. |
| Large datasets (10k+ leads) | Virtualize NeonTable rows (TanStack Virtual). Pipeline DAG stays small (fixed 5-7 nodes). No 3D scaling concern. |

### Scaling Priorities

1. **First bottleneck: Bundle size.** Without lazy loading, initial load balloons from ~200KB to ~1MB+. Code splitting at route level is the fix, built into the architecture from Phase 0.

2. **Second bottleneck: GPU memory on sustained use.** If R3F scenes leak geometries/materials on page transitions, GPU memory grows until the tab crashes. Fix: every scene component must dispose resources in cleanup (`useEffect` return). Use drei's `useTexture`/`useGLTF` which handle disposal automatically.

## Sources

- React Three Fiber Canvas API and Suspense patterns — Context7 `/pmndrs/react-three-fiber` (HIGH confidence)
- React Three Fiber scaling/performance docs — Context7 `/pmndrs/react-three-fiber` (HIGH confidence)
- Drei helpers (Float, Sparkles, Stars, Environment, Text3D) — Context7 `/pmndrs/drei` (HIGH confidence)
- React Postprocessing (Bloom, ChromaticAberration, EffectComposer) — Context7 `/pmndrs/react-postprocessing` (HIGH confidence)
- @xyflow/react custom nodes, edges, elkjs layout — Context7 `/websites/reactflow_dev` (HIGH confidence)
- Motion v12 AnimatePresence, layout animations — Context7 `/websites/motion_dev_react` (HIGH confidence)
- Existing Syntrix dashboard source code — direct file reads (HIGH confidence)

---
*Architecture research for: Cyberpunk immersive 3D dashboard progressive upgrade*
*Researched: 2026-02-24*
