# Roadmap: Syntrix Cyberpunk Dashboard

**Created:** 2026-02-24
**Phases:** 7
**Requirements:** 42 mapped
**Depth:** Comprehensive
**Parallelization:** Yes (up to 4 terminals)

## Phase Overview

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | CSS Foundation & Design System | Establish cyberpunk visual identity and architectural guardrails | DS-01..DS-07 | 5 |
| 2 | Cyberpunk Component Library | Build reusable cyberpunk primitives for all pages | CL-01..CL-07 | 4 |
| 3 | Ambient Effects & Motion Layer | Transform navigation feel with particles, transitions, stagger | AE-01..AE-05 | 4 |
| 4 | Dashboard & Analytics Pages | First visual wow moment — prove component library end-to-end | DP-01..DP-03, AP-01..AP-03 | 3 |
| 5 | Pipeline Visualization | Core differentiator — animated node graph with data flow | PV-01..PV-08 | 5 |
| 6 | Hero 3D Scene & Remaining Pages | Complete all 6 pages + 3D hero background | HS-01..HS-03, RP-01..RP-04 | 4 |
| 7 | Performance & Polish | Bundle verification, WCAG audit, GPU stability, performance mode | PP-01..PP-07 | 5 |

## Parallel Execution Strategy

**4 terminals recommended.** Phases have dependencies but several can overlap:

```
Timeline:
  T1: [Phase 1] ──────> [Phase 4: Dashboard+Analytics] ──> [Phase 7: Polish]
  T2: [Phase 1] ──────> [Phase 2: Components] ─────────────────────> [Phase 6: Remaining Pages]
  T3:              wait > [Phase 3: Ambient Effects] ───────> [Phase 6: Hero 3D]
  T4:              wait > [Phase 5: Pipeline Viz (2D)] ─────> [Phase 5: Pipeline Viz (3D)]

Dependencies:
  Phase 1 → Phase 2, Phase 3, Phase 4 (all need CSS vars)
  Phase 2 → Phase 4, Phase 6 (pages need components)
  Phase 3 → Phase 4 (pages need transitions)
  Phase 5 → Phase 6 Hero 3D (R3F patterns established)
  All → Phase 7 (polish after everything built)
```

## Phase Details

---

### Phase 1: CSS Foundation & Design System

**Goal:** Establish the cyberpunk visual identity via CSS custom properties, initialize shadcn/ui, create CyberpunkLayout wrapper, and set architectural guardrails for 3D (lazy-load boundaries, single-canvas strategy, ref-based animation convention).

**Requirements:** DS-01, DS-02, DS-03, DS-04, DS-05, DS-06, DS-07

**Success Criteria:**
1. All 6 existing pages render through CyberpunkLayout with cyberpunk color palette applied — no visual regression in functionality
2. Glassmorphism utility classes produce frosted glass effect on any card element
3. Neon glow appears on button/link hover and input focus states
4. Scanline overlay visible as subtle CRT texture across panels
5. shadcn/ui CLI installed and configured with cyberpunk oklch theme variables

**Deliverables:**
- `dashboard/src/styles/cyberpunk-vars.css` — CSS custom properties (colors, glow, glass)
- `dashboard/src/styles/scanlines.css` — CRT overlay effect
- `dashboard/src/styles/glassmorphism.css` — glass utility classes
- `dashboard/src/layouts/CyberpunkLayout.tsx` — new root layout
- shadcn/ui initialized with `components.json` and cyberpunk theme
- `dashboard/src/lib/lazy-3d.ts` — lazy-load utilities for future 3D imports

**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md -- Install dependencies, configure path aliases, shadcn/ui init, CSS design system (palette, glassmorphism, scanlines, glow, typography)
- [ ] 01-02-PLAN.md -- CyberpunkLayout wrapper, lazy-3d utility, route swap, visual verification

**Terminal:** T1 (then T2 joins after)

---

### Phase 2: Cyberpunk Component Library

**Goal:** Build the full set of cyberpunk UI primitives that all page upgrades depend on. Install Motion v12 and create shared animation presets.

**Requirements:** CL-01, CL-02, CL-03, CL-04, CL-05, CL-06, CL-07

**Success Criteria:**
1. GlassCard renders with glassmorphism + optional augmented-ui clip-path border
2. NeonMetricCard displays animated counting number with glow effect
3. NeonTable renders with hover row glow and neon-styled headers
4. All components respect cyberpunk CSS variables from Phase 1

**Deliverables:**
- `dashboard/src/components/cyber/GlassCard.tsx`
- `dashboard/src/components/cyber/NeonMetricCard.tsx`
- `dashboard/src/components/cyber/NeonSidebar.tsx`
- `dashboard/src/components/cyber/NeonBadge.tsx` + `NeonButton.tsx`
- `dashboard/src/components/cyber/NeonTable.tsx`
- `dashboard/src/components/cyber/NeonInput.tsx` + `NeonTooltip.tsx`
- `dashboard/src/lib/animation-presets.ts` — shared Motion variants
- `package.json` updated with `motion`, `augmented-ui`

**Terminal:** T2 (after Phase 1 complete)

---

### Phase 3: Ambient Effects & Motion Layer

**Goal:** Transform navigation feel globally — particle backgrounds, page transitions, staggered mounts, accessibility support.

**Requirements:** AE-01, AE-02, AE-03, AE-04, AE-05

**Success Criteria:**
1. Floating particles visible in background across all pages
2. Page transitions animate (fade+slide) when navigating between routes
3. Components stagger-mount on page load with "initializing" feel
4. All animations disabled when OS prefers-reduced-motion is set

**Deliverables:**
- `dashboard/src/components/effects/ParticleBackground.tsx`
- `dashboard/src/components/effects/PageTransition.tsx`
- `dashboard/src/components/effects/Scanlines.tsx`
- `dashboard/src/hooks/useReducedMotion.ts`
- Router updated with AnimatePresence wrapper
- `package.json` updated with `@tsparticles/react`, `tsparticles`

**Terminal:** T3 (after Phase 1 complete)

---

### Phase 4: Dashboard & Analytics Page Upgrades

**Goal:** First visual wow moment — Dashboard and Analytics pages fully cyberpunk-styled with neon charts and animated counters.

**Requirements:** DP-01, DP-02, DP-03, AP-01, AP-02, AP-03

**Success Criteria:**
1. Dashboard metric cards use NeonMetricCard with animated counters
2. All Recharts use neon gradient fills (pink→orange) with glassmorphism tooltips
3. Analytics query table uses NeonTable with glow highlights

**Deliverables:**
- `dashboard/src/pages/Dashboard.tsx` — upgraded
- `dashboard/src/pages/Analytics.tsx` — upgraded
- `dashboard/src/lib/chart-theme.ts` — shared neon chart configuration
- `dashboard/src/components/cyber/CyberBarChart.tsx`
- `dashboard/src/components/cyber/CyberFunnelChart.tsx`

**Terminal:** T1 (after Phases 1+2+3 complete)

---

### Phase 5: Pipeline Visualization (Hero Feature)

**Goal:** Build the core differentiator — animated pipeline node graph with 2D DAG and 3D scene, connected to real-time WebSocket data.

**Requirements:** PV-01, PV-02, PV-03, PV-04, PV-05, PV-06, PV-07, PV-08

**Success Criteria:**
1. usePipelineFlow() hook returns normalized PipelineFlowData from existing stats + WebSocket
2. 2D DAG renders pipeline stages as custom neon nodes with animated edges showing flow direction
3. 3D scene renders pipeline as glowing orbs with particle streams between stages
4. WebSocket events trigger visible animations (new items entering flow)
5. Toggle switch allows user to choose 2D or 3D visualization

**Deliverables:**
- `dashboard/src/hooks/usePipelineFlow.ts` — adapter hook
- `dashboard/src/pipeline/PipelineDAG.tsx` — @xyflow/react 2D view
- `dashboard/src/pipeline/StageNode.tsx` — custom node component
- `dashboard/src/pipeline/DataEdge.tsx` — custom animated edge
- `dashboard/src/pipeline/pipeline-layout.ts` — elkjs layout config
- `dashboard/src/scenes/PipelineScene.tsx` — R3F 3D view (lazy)
- `dashboard/src/scenes/StageOrb.tsx` — 3D stage geometry
- `dashboard/src/scenes/PipelineParticles.tsx` — instanced particles
- `dashboard/src/pages/PipelineLive.tsx` — new page with 2D/3D toggle
- `package.json` updated with `@xyflow/react`, `elkjs`, `@react-three/fiber`, `@react-three/drei`, `@react-three/postprocessing`, `three`

**Terminal:** T4 (after Phase 1 complete; 3D portion after Phase 3)

---

### Phase 6: Hero 3D Scene & Remaining Pages

**Goal:** Complete all 6 pages with cyberpunk styling. Add 3D hero background behind Dashboard. Implement GPU tier adaptive quality.

**Requirements:** HS-01, HS-02, HS-03, RP-01, RP-02, RP-03, RP-04

**Success Criteria:**
1. 3D hero scene renders abstract animated geometry behind Dashboard content with selective bloom
2. useGPUTier returns quality tier and pages adapt (HIGH/MEDIUM/LOW)
3. Leads and Experiments pages use NeonTable
4. Queue page uses GlassCard-based DraftCards with neon action buttons

**Deliverables:**
- `dashboard/src/scenes/HeroScene.tsx` — R3F abstract background (lazy)
- `dashboard/src/hooks/useGPUTier.ts` — GPU detection + quality tiers
- `dashboard/src/pages/Leads.tsx` — upgraded
- `dashboard/src/pages/Queue.tsx` — upgraded
- `dashboard/src/pages/Experiments.tsx` — upgraded
- `dashboard/src/pages/Settings.tsx` — upgraded

**Terminal:** T2 (pages) + T3 (hero 3D, after Phase 5 R3F patterns established)

---

### Phase 7: Performance & Polish

**Goal:** Bundle verification, accessibility audit, GPU memory stability, performance mode toggle. Ship-ready quality gate.

**Requirements:** PP-01, PP-02, PP-03, PP-04, PP-05, PP-06, PP-07

**Success Criteria:**
1. Initial bundle under 200KB (3D lazy-loaded in separate chunk)
2. Single persistent Canvas confirmed (no per-page Canvas instances)
3. GPU memory stable over 30-minute navigation session (no leaks)
4. All text passes WCAG AA contrast against cyberpunk backgrounds
5. "Performance Mode" toggle in Settings disables 3D/particles

**Deliverables:**
- `vite.config.ts` updated with `manualChunks` for vendor-3d isolation
- `dashboard/src/hooks/useDisposable.ts` — GPU memory disposal utility
- WCAG contrast verification report
- Performance mode toggle in Settings page
- All 4 existing test files passing

**Terminal:** All terminals (after Phases 1-6 complete)

---

## Requirement Coverage

All 42 v1 requirements mapped to exactly one phase. 0 unmapped. ✓

---
*Roadmap created: 2026-02-24*
*Last updated: 2026-02-24 after initial creation*
