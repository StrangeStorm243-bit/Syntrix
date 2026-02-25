# Terminal D — Pipeline Visualization (Hero Feature)

**Role:** Build the core differentiator — animated pipeline node graph with 2D DAG and 3D scene
**Phases:** 5 (full)
**Waits for:** Terminal A Phase 1 complete

---

## Shared Conventions

See `v03terminalA.md` → "Shared Conventions" section for color palette, typography, file naming, import conventions, architectural rules, and coordination protocol. ALL terminals follow the same conventions.

---

## Phase 5: Pipeline Visualization

**Requirements:** PV-01, PV-02, PV-03, PV-04, PV-05, PV-06, PV-07, PV-08

This is the largest and most complex phase. It has 3 internal stages:
1. **Data layer** (hooks + types) — testable without UI
2. **2D DAG** (@xyflow/react) — first visual milestone
3. **3D scene** (R3F) — final wow factor

### Stage 1: Data Layer

#### Step 1: Install Dependencies

```bash
cd dashboard
npm install @xyflow/react elkjs
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing
npm install -D @types/three
```

#### Step 2: Define Pipeline Data Types

**File: `dashboard/src/pipeline/types.ts`**

```typescript
export interface PipelineStage {
  id: string;                    // 'collect' | 'normalize' | 'judge' | 'score' | 'draft' | 'send'
  label: string;                 // 'Collect' | 'Normalize' | ...
  count: number;                 // items processed in this stage
  active: boolean;               // currently processing?
  color: string;                 // neon color for this stage
}

export interface PipelineEdge {
  source: string;
  target: string;
  throughput: number;            // items/min flowing through
  animated: boolean;
}

export interface PipelineEvent {
  id: string;
  type: 'item_entered' | 'item_completed' | 'item_failed';
  stage: string;
  timestamp: number;
  detail: string;
}

export interface PipelineFlowData {
  stages: PipelineStage[];
  edges: PipelineEdge[];
  events: PipelineEvent[];       // recent events (buffered, max 5/sec)
  isLive: boolean;               // WebSocket connected?
}
```

#### Step 3: Create usePipelineFlow Hook

**File: `dashboard/src/hooks/usePipelineFlow.ts`**

```typescript
// Combines:
//   - useStats() → stage counts (collected, judged, scored, drafted, sent)
//   - useWebSocket() → real-time pipeline_progress events
//
// Returns: PipelineFlowData
//
// Stage mapping from useStats():
//   stages = [
//     { id: 'collect', label: 'Collect', count: stats.collected, color: '#ff1493' },
//     { id: 'judge', label: 'Judge', count: stats.judged, color: '#ff6b35' },
//     { id: 'score', label: 'Score', count: stats.scored, color: '#ffd700' },
//     { id: 'draft', label: 'Draft', count: stats.drafted, color: '#ff1493' },
//     { id: 'send', label: 'Send', count: stats.sent, color: '#ff6b35' },
//   ]
//
// Edge generation:
//   edges = stages.slice(0, -1).map((s, i) => ({
//     source: s.id, target: stages[i+1].id,
//     throughput: Math.min(s.count, stages[i+1].count),
//     animated: true,
//   }))
//
// WebSocket event buffering:
//   - Max 5 events per second (throttle)
//   - Buffer incoming pipeline_progress messages
//   - Map to PipelineEvent type
//   - Keep last 50 events in circular buffer
//
// Fallback: if WebSocket disconnected, stages still populate from useStats() polling
```

### Stage 2: 2D Pipeline DAG (@xyflow/react)

#### Step 4: Create Pipeline Layout Config

**File: `dashboard/src/pipeline/pipeline-layout.ts`**

```typescript
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

// ELK options for horizontal left-to-right pipeline:
const layoutOptions = {
  'elk.algorithm': 'layered',
  'elk.direction': 'RIGHT',
  'elk.spacing.nodeNode': '80',
  'elk.layered.spacing.nodeNodeBetweenLayers': '120',
};

export async function computeLayout(stages: PipelineStage[]): Promise<LayoutResult> {
  // Convert stages to ELK graph
  // Run elk.layout()
  // Return node positions + edge routes
}
```

#### Step 5: Create Custom Stage Node

**File: `dashboard/src/pipeline/StageNode.tsx`**

```typescript
// Custom @xyflow/react node component
// Props: data (PipelineStage from types.ts)
//
// Visual design:
//   - GlassCard base with augmented-ui clip-path border
//   - Stage icon at top (lucide-react: Download, Brain, BarChart3, FileText, Send)
//   - Stage label in monospace
//   - Count displayed with NeonMetricCard-style animated number
//   - Color-coded neon border matching stage.color
//   - Pulsing glow when stage.active === true
//   - Handles on left (input) and right (output) with neon dot
//
// Size: ~160px wide x ~120px tall
```

#### Step 6: Create Custom Animated Edge

**File: `dashboard/src/pipeline/DataEdge.tsx`**

```typescript
// Custom @xyflow/react edge component
// IMPORTANT: Do NOT use stroke-dasharray animation (CPU-bound)
// Instead use SVG <animateMotion> for a particle flowing along the path
//
// Visual design:
//   - Base path: thin line, color rgba(255, 20, 147, 0.3)
//   - Animated particle: small circle (r=3) with neon glow filter
//   - Particle travels from source to target along edge path
//   - Duration: inversely proportional to throughput (more flow = faster)
//   - Multiple particles if throughput > threshold
//
// Implementation:
//   <path d={edgePath} stroke="rgba(255,20,147,0.3)" />
//   <circle r="3" fill="#ff1493">
//     <animateMotion dur={`${duration}s`} repeatCount="indefinite">
//       <mpath href={`#edge-path-${id}`} />
//     </animateMotion>
//   </circle>
//   <filter id="glow"><feGaussianBlur stdDeviation="2" /><feMerge>...</feMerge></filter>
```

#### Step 7: Create Pipeline DAG Component

**File: `dashboard/src/pipeline/PipelineDAG.tsx`**

```typescript
// Uses @xyflow/react
// Props: data (PipelineFlowData)
//
// Features:
//   - Custom node types: { stage: StageNode }
//   - Custom edge types: { data: DataEdge }
//   - Auto-layout via elkjs (computeLayout from pipeline-layout.ts)
//   - Dark background (--bg-void)
//   - Minimap with neon colors
//   - Zoom/pan controls with NeonButton styling
//   - Fitview on mount
//   - React to PipelineFlowData changes (update counts, add events)
//
// Performance:
//   - Memoize node/edge arrays
//   - Only re-layout when stage count changes (not on every event)
```

#### Step 8: Create Activity Feed

**File: `dashboard/src/pipeline/ActivityFeed.tsx`**

```typescript
// Real-time scrolling list of pipeline events
// Props: events (PipelineEvent[])
//
// Visual design:
//   - GlassCard container with fixed height (scrollable)
//   - Each event: timestamp (monospace) + stage badge + detail text
//   - New events animate in from top (Motion slideDown)
//   - Color-coded by stage
//   - "LIVE" indicator with pulsing green/pink dot when WebSocket connected
```

### Stage 3: 3D Pipeline Scene (R3F)

#### Step 9: Create Stage Orb

**File: `dashboard/src/scenes/StageOrb.tsx`**

```typescript
// R3F component — a 3D representation of a pipeline stage
// Props: position, color, label, count, active, scale
//
// Visual:
//   - Sphere geometry (or icosahedron for faceted look)
//   - MeshStandardMaterial with emissive matching stage color
//   - Wireframe overlay (second mesh, slightly larger)
//   - drei <Text> label floating above
//   - drei <Float> for subtle bobbing
//   - When active: emissive intensity pulses (useFrame + ref)
//
// CRITICAL: All animation via useFrame + useRef, NEVER useState
```

#### Step 10: Create Pipeline Particles

**File: `dashboard/src/scenes/PipelineParticles.tsx`**

```typescript
// R3F instanced particle system for data flowing between stages
// Props: edges (source/target positions + throughput)
//
// Technique (from Shopify BFCM):
//   - InstancedMesh with N particles (N = sum of throughputs, capped at 200)
//   - Each particle has: startPos, endPos, progress (0→1), speed
//   - useFrame updates progress, moves particle along bezier curve between stages
//   - When progress >= 1, reset to 0 (loop)
//   - Color: interpolate from source stage color to target stage color
//   - Size: small (0.02 world units)
//   - Emissive: yes (for bloom glow)
//
// Performance:
//   - Single draw call for all particles (instanced)
//   - Positions updated via instanceMatrix, not React state
//   - Cap particle count based on GPU tier
```

#### Step 11: Create Pipeline 3D Scene

**File: `dashboard/src/scenes/PipelineScene.tsx`**

```typescript
// R3F Canvas with full pipeline visualization
// Props: data (PipelineFlowData)
// MUST be lazy-loaded via lazy3D()
//
// Scene:
//   - Camera: PerspectiveCamera, positioned to see all stages
//   - OrbitControls (drei) — user can rotate/zoom
//   - Environment: dark, subtle ambient light
//   - StageOrb for each stage (positioned in arc or line)
//   - PipelineParticles for data flow between stages
//   - Post-processing:
//     <EffectComposer>
//       <Bloom luminanceThreshold={0.5} intensity={1.2} levels={5} />
//     </EffectComposer>
//
// Data flow:
//   - Map PipelineFlowData.stages to StageOrb positions
//   - Map PipelineFlowData.edges to PipelineParticles configs
//   - New events (from WebSocket) spawn burst of particles at source stage
```

#### Step 12: Create Pipeline Live Page

**File: `dashboard/src/pages/PipelineLive.tsx`**

```typescript
// New page — accessible at /pipeline route
//
// Layout:
//   - Full-width main area: PipelineDAG (2D) or PipelineScene (3D)
//   - Toggle switch in top-right: "2D / 3D" (stores preference in localStorage)
//   - Right sidebar or bottom panel: ActivityFeed
//   - Header: "Pipeline Live" + connection status indicator
//
// Data:
//   - usePipelineFlow() hook for all data
//   - Pass data to whichever visualization is active
//
// 3D loaded lazily:
//   const PipelineScene3D = lazy3D(() => import('../scenes/PipelineScene'));
//   Only imported when user selects 3D mode
```

#### Step 13: Add Route & Navigation

Update `App.tsx`: add `/pipeline` route pointing to `PipelineLive`.
Update `NeonSidebar` (Terminal B): add "Pipeline" nav link with Activity icon.

#### Step 14: Verify & Commit

**2D milestone verification:**
- Pipeline DAG renders all 5 stages with correct counts from API
- Edges show animated particles flowing left-to-right
- Activity feed scrolls with mock events
- elkjs layout positions nodes correctly

**3D milestone verification:**
- 3D scene renders glowing orbs for each stage
- Particles flow between stages along curved paths
- Bloom makes everything glow
- Toggle switch swaps between 2D and 3D
- WebSocket events trigger visible particle bursts

```bash
git commit -m "feat(dashboard): Phase 5 — pipeline visualization (2D DAG + 3D scene + real-time feed)"
```

**Signal to Terminal C: R3F patterns established. HeroScene can use same patterns.**

---

## Phase 7 Responsibilities (Terminal D)

Terminal D owns in Phase 7:
1. **Single Canvas verification** — confirm no per-page Canvas instances leak
2. **useRef animation audit** — grep for `useState` inside any `useFrame` callback
3. **Pipeline performance** — verify 60fps with 200 particles on integrated GPU
4. **WebSocket throttle** — verify event buffer caps at 5/sec even under flood
5. **Performance Mode** — when toggled, pipeline falls back to 2D-only (no R3F loaded)
