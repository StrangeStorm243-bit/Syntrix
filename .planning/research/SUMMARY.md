# Project Research Summary

**Project:** Syntrix — Cyberpunk Immersive 3D Dashboard
**Domain:** Progressive visual upgrade of existing React 19 SPA to cyberpunk/sci-fi aesthetic with 3D pipeline visualization
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

This project upgrades the existing Syntrix dashboard (a React 19 + Vite 7 + Tailwind 4 SPA) from a standard dark-mode UI to a cyberpunk immersive experience. The domain is well-understood: industry references (Shopify BFCM engineering, ARWES framework, Cyberpunk 2077 UI analysis) establish clear patterns for what makes a "cyberpunk dashboard" convincing versus what merely applies dark styling with colored accents. The recommended approach is strictly progressive and layered — CSS foundation first (color tokens, glassmorphism, scanlines), then motion and 2D interaction, then 3D scenes as a final differentiated layer. The existing data layer (TanStack Query, WebSocket, FastAPI) remains completely unchanged throughout.

The core differentiator is a pipeline visualization — the collect→judge→score→draft→send pipeline rendered as an animated node graph with data flowing between stages. Research confirms @xyflow/react (for 2D DAG layout) and React Three Fiber v9 (for 3D scenes) are the right tools, with clear rationale: R3F v9 is explicitly designed for React 19, and @xyflow handles directed acyclic graphs deterministically unlike force-graph libraries. The recommended stack has been verified for React 19 + Tailwind 4 compatibility at every layer — no guessing.

The primary risks are architectural and must be decided before any 3D code is written: (1) a single persistent WebGL canvas at layout level (not per-page) to avoid browser context exhaustion limits, (2) lazy-loading all Three.js dependencies to prevent 600KB+ initial bundle regression, and (3) establishing ref-based animation patterns to prevent 60fps React re-render cascades inside `useFrame`. These are Phase 1 foundations — retrofitting them later is expensive. Accessibility (WCAG contrast, `prefers-reduced-motion`) and performance degradation paths (GPU tier detection, SelectiveBloom) must be built in from the start, not added as afterthoughts.

## Key Findings

### Recommended Stack

The existing stack (React 19.2, Vite 7, TypeScript 5.9, Tailwind 4, TanStack Query 5, Recharts 3) is retained and extended — nothing is replaced. The additions are carefully versioned for React 19 compatibility. R3F v9 is the only React 3D renderer with explicit React 19 support. Motion v12 (formerly Framer Motion) works with React 19 but its Three.js integration (`motion/three`) does NOT — GSAP fills the 3D animation role instead, using a ref-based bridge pattern to avoid reconciler conflicts. shadcn/ui provides the component foundation via CSS variable overrides (oklch color space maps cleanly to the neon palette). See `.planning/research/STACK.md` for full version matrix and installation commands.

**Core technologies:**
- `three@^0.183.1` + `@react-three/fiber@^9.5.0`: 3D rendering — R3F v9 is the only production-grade React 3D renderer with confirmed React 19 compatibility
- `@react-three/drei@^10.7.7` + `@react-three/postprocessing@^3.0.4`: 3D helpers and bloom/chromatic aberration effects — eliminates boilerplate, pairs with R3F v9
- `@xyflow/react@^12.10.1` + `elkjs@^0.11.0`: Pipeline DAG visualization — designed for directed graphs with deterministic layouts, unlike force-graph alternatives
- `motion@^12.34.3`: 2D React UI animations — 18M+/month downloads, React 19 compatible, import from `motion/react`
- `gsap@^3.14.2` + `@gsap/react@^2.1.2`: Complex sequenced timelines and 3D animation — GSAP is now fully free including all bonus plugins; `useGSAP()` hook handles cleanup
- `shadcn/ui` (CLI): Component foundation — copy-paste model gives full theming ownership; CSS variable system maps directly to neon palette
- `augmented-ui@^2.0.0`: HUD clip-path borders — pure CSS, 150+ tested clip-path combinations for sci-fi panel aesthetics
- `cybercore-css@^0.7.0`: Scanlines, glitch, noise effects — pure CSS/SCSS, zero JS overhead

**Key compatibility warnings:** `motion/three` is React 18 only — do not use with React 19. ARWES is alpha, React strict mode incompatible, React 18 only. Theatre.js React 19 compatibility is unconfirmed — defer.

### Expected Features

Research identifies a clear hierarchy between CSS-only table stakes (immediate, cheap, highest visual impact), motion/interaction differentiators (medium effort, high value), and 3D headline features (high effort, core proposition). See `.planning/research/FEATURES.md` for full prioritization matrix.

**Must have (table stakes — without these it's just a dark theme, not cyberpunk):**
- Dark void background (`#0a0608`) + warm neon color system (hot pink / orange / gold) — the defining visual signature
- Glassmorphism panels (`backdrop-blur` + translucent background + subtle border) — universal in cyberpunk reference material
- Neon glow on interactive elements (hover/focus via `box-shadow`) — static neon without glow reads as flat
- Scanline/noise overlay — single `::after` pseudo-element, CRT fingerprint of the genre, zero performance cost
- Neon-styled Recharts (gradient fills, glow, glassmorphism tooltips) — current cold blue charts break the aesthetic
- Animated number counters on metric cards — static numbers on a "futuristic" dashboard feels broken
- Monospace typography for data values — HUD readability standard

**Should have (differentiators that create the "wow" factor):**
- 3D pipeline node graph with animated data flow — the core proposition, no competitor visualizes ML pipelines this way
- 3D hero background scene (R3F Canvas behind Dashboard content) — depth that CSS cannot match
- Real-time WebSocket activity feed with animated list — existing hook wiring, makes dashboard feel alive
- HUD clipped card borders (augmented-ui) — visual language of sci-fi movie interfaces
- Page transitions with Motion AnimatePresence — immersion-breaking without them
- Staggered mount animations — "system initializing" feel on page load
- Post-processing bloom + chromatic aberration — makes neon physically glow in 3D scenes

**Defer to v2+:**
- 3D pipeline particle flow (R3F instanced particles replacing 2D @xyflow) — 2D version provides 80% of value at 20% of cost
- Sound effects — polarizing, requires opt-in, needs sound assets/licensing
- GSAP complex intro timelines — 45KB bundle weight, justifiable only for hero moments
- Responsive 2D mobile fallback — primary use case is desktop
- Animated beams between elements (Magic UI AnimatedBeam) — fragile with responsive layouts

**Anti-features (deliberately excluded):**
- Aggressive or continuous glitch effects — eye strain, photosensitivity risk
- 3D perspective charts — distorts data perception, universally condemned by data viz experts
- Auto-playing sound — universally hated, violates accessibility guidelines
- Light mode / theme switcher — doubles CSS work, undermines the entire aesthetic
- Parallax scrolling on data pages — causes motion sickness, breaks scroll usability

### Architecture Approach

The architecture is a four-layer progressive overlay on top of the unchanged existing system. The Design System layer (CSS variables, Tailwind theme) is the foundation — all other layers reference it without JS coupling. The Component layer houses cyberpunk primitives (`components/cyber/`) isolated from existing components. The Presentation layer adds new directories (`scenes/` for R3F, `pipeline/` for @xyflow, `effects/` for ambient CSS effects). The Data layer is completely unchanged. The critical architectural decisions are: (1) all R3F code is isolated in `scenes/` and lazy-loaded, never in the main bundle; (2) a single persistent `<Canvas>` at layout level to avoid WebGL context limits; (3) a `usePipelineFlow()` adapter hook decouples visualization from API shape; (4) GSAP and Motion never animate the same DOM nodes; (5) CSS transitions handle hover/focus, Motion handles enter/exit, R3F `useFrame` handles continuous 3D loops. See `.planning/research/ARCHITECTURE.md` for detailed component responsibilities, data flow diagrams, and code examples.

**Major components:**
1. `CyberpunkLayout` — root layout wrapper, mounts ambient effects, scopes CSS design tokens, wraps `<Outlet />`
2. `components/cyber/` — GlassCard, NeonMetricCard, NeonSidebar, NeonTable, NeonButton: cyberpunk primitives used across all pages
3. `scenes/` — HeroScene, PipelineScene, PipelineParticles, StageOrb, effects: all R3F WebGL code, lazy-loaded, isolated
4. `pipeline/` — PipelineDAG, StageNode, DataEdge, pipeline-layout: @xyflow/react DAG components, also lazy-loaded
5. `usePipelineFlow()` — adapter hook combining `useStats()` + `useWebSocket()` into `PipelineFlowData` shape consumed by both 2D and 3D pipeline views
6. `styles/` — cyberpunk-vars.css, augmented-ui.css, scanlines.css, glassmorphism.css: CSS-only tokens loaded globally

### Critical Pitfalls

Research identified 8 pitfalls, with 5 that must be addressed in Phase 1 before any 3D code is written:

1. **React state in animation loop** — calling `setState` inside `useFrame` causes 60 re-renders/second. Use `useRef` for all animation-speed values; mutate `ref.current` directly. Establish this convention in the first `useFrame` usage.

2. **WebGL context exhaustion (browser limit: 8-16 contexts)** — per-page `<Canvas>` instances accumulate across navigation and silently kill old contexts (black screens on Safari). Mandate a single persistent `<Canvas>` at layout level using drei's `<View>` for routing scene content.

3. **GPU memory leaks from undisposed Three.js resources** — geometries, materials, and textures are NOT auto-GC'd. Create a `useDisposable` utility hook in Phase 1 and apply it to every 3D component. Monitor `renderer.info.memory` during development.

4. **Bundle size explosion** — Three.js (~600KB) + drei (~200KB) + postprocessing (~150KB) + elkjs (~300KB) = 1MB+ if statically imported. All 3D imports must be behind `React.lazy()` from the first commit. Vite `manualChunks` isolates into `vendor-3d` chunk. Target: initial chunk under 200KB.

5. **Neon aesthetic destroying text readability** — neon colors can fail WCAG 2.1 AA (4.5:1 contrast). Data text (table cells, metric values) must use verified warm white (`#ffe0ec`). Run every color combination through contrast checker when establishing the color system.

Additional pitfalls for Phase 2+: bloom performance on integrated GPUs (use SelectiveBloom + PerformanceMonitor), React Flow animated edges CPU bottleneck (use `<animateMotion>` not `stroke-dasharray`), GSAP/R3F reconciler conflicts (GSAP = DOM layer only, never touches Three.js objects directly), unthrottled WebSocket→3D updates (buffer to max 5 particle spawns/second).

## Implications for Roadmap

Research strongly suggests a 7-phase structure driven by architectural dependencies. The ordering is not arbitrary — each phase produces artifacts consumed by later phases.

### Phase 1: CSS Foundation and Design System
**Rationale:** Color tokens and CSS variables must exist before any cyberpunk component can reference them. This phase costs almost nothing (pure CSS + lightweight React components) but produces the highest visual impact-per-hour of any phase. Also the mandatory moment to establish all Phase 1 architectural guardrails (canvas strategy, lazy-load boundaries, disposal patterns, animation tool hierarchy).
**Delivers:** Global cyberpunk palette, glassmorphism utility classes, scanline overlay, neon glow states, monospace data typography, `CyberpunkLayout` wrapper, shadcn/ui initialization with cyberpunk theme. All existing pages render through new layout with no visual regression (parity checkpoint before any page changes).
**Addresses:** All P1 table-stakes features from FEATURES.md (dark void background, neon color system, glassmorphism panels, neon glow, scanlines, monospace typography)
**Avoids:** Bundle size explosion (lazy-load architecture established here), WCAG contrast failures (color tokens verified before any page uses them), WebGL context exhaustion (single-canvas decision made here), GSAP/R3F conflict (tool boundaries documented here)

### Phase 2: Cyberpunk Component Library
**Rationale:** Pages cannot be upgraded until cyberpunk primitives exist. Build the library before touching any page — this enables parallel page upgrades in later phases without blocking on component work.
**Delivers:** `components/cyber/` — GlassCard, NeonMetricCard, NeonSidebar, NeonBadge, NeonButton, NeonTable, NeonInput, NeonTooltip, PageTransition. Motion v12 installed. animation-presets.ts with shared enter/exit variants.
**Uses:** shadcn/ui base components (from Phase 1), augmented-ui (clip-path borders), Motion v12 (enter/exit animations)
**Implements:** Component + Animation layer from architecture

### Phase 3: Ambient Effects and Motion Layer
**Rationale:** Page transitions and staggered animations require Motion to be installed and `AnimatePresence` to be in the router. Particle background mounts in `CyberpunkLayout` which already exists. This transforms the "feel" of navigation globally before any individual page is touched.
**Delivers:** ParticleBackground (tsParticles) in layout, PageTransition AnimatePresence on router, Scanlines component, `useReducedMotion` accessibility hook, staggered mount animation presets
**Addresses:** Animated page transitions, ambient particle background, glitch effects infrastructure, accessibility (`prefers-reduced-motion`)

### Phase 4: Dashboard and Analytics Page Upgrades
**Rationale:** Dashboard and Analytics are the highest-traffic pages with the most visual impact. Upgrading them first proves the component library works end-to-end and delivers the first "wow" moment. NeonMetricCard, CyberBarChart, CyberFunnelChart are built here.
**Delivers:** Dashboard page fully cyberpunk-styled (NeonMetricCard grid, neon Recharts, animated counters), Analytics page with CyberBarChart/CyberFunnelChart wrappers, chart-theme.ts with shared neon gradient tokens
**Uses:** NeonMetricCard + GlassCard (from Phase 2), Motion stagger (from Phase 3), Recharts (existing — restyled not replaced)
**Implements:** Chart wrapper layer from architecture

### Phase 5: Pipeline Visualization (Hero Feature)
**Rationale:** The core differentiating feature. Built after component and motion foundations are in place. Sequenced internally: data types first (testable without UI), then 2D DAG (milestone: working pipeline view), then 3D scene upgrade (milestone: animated 3D flow). The 2D @xyflow view and 3D R3F scene share only the `usePipelineFlow()` data contract — they never share components.
**Delivers:** `usePipelineFlow()` adapter hook, PipelineDAG with custom StageNode/DataEdge (@xyflow + elkjs), PipelineScene with StageOrb + PipelineParticles (R3F), `PipelineLive` page with 2D/3D toggle, WebSocket activity feed connected
**Uses:** @xyflow/react + elkjs, R3F + drei + postprocessing (all lazy-loaded), existing useWebSocket hook
**Avoids:** React state in animation loop (useRef pattern), WebGL context limit (single canvas), GPU memory leaks (useDisposable), React Flow edge CPU bottleneck (animateMotion not stroke-dasharray), WebSocket update flood (buffered to 5/sec)

### Phase 6: Dashboard Hero 3D Scene and Remaining Pages
**Rationale:** HeroScene (R3F abstract geometry behind Dashboard) builds on R3F patterns established in Phase 5. Remaining pages (Leads, Queue, Experiments, Settings) are parallel component swaps — they only depend on Phase 2 (cyber components exist). Phase 5 and Phase 6 page work can run in parallel.
**Delivers:** HeroScene with bloom postprocessing behind Dashboard metric grid, useGPUTier hook with quality tiers, all 6 pages fully cyberpunk-styled (NeonTable on Leads/Experiments, GlassCard on Queue, NeonInput on Settings)
**Implements:** GPU adaptive quality pattern (HIGH = full postprocessing, MEDIUM = no postprocessing, LOW = 2D static fallback)

### Phase 7: Performance and Polish
**Rationale:** Polish and performance tuning must come after the complete experience exists. Cannot optimize what hasn't been built.
**Delivers:** Lighthouse performance audit with verified initial chunk under 200KB, `vite-bundle-visualizer` in CI, PerformanceMonitor-driven bloom disabling, verified WCAG AA on all 6 pages, `prefers-reduced-motion` comprehensive testing, GPU memory stability over 30-minute navigation sessions, "Performance Mode" toggle in Settings
**Addresses:** All "Looks Done But Isn't" checklist items from PITFALLS.md

### Phase Ordering Rationale

- CSS foundation must precede components, which must precede pages — this is a strict dependency chain
- The single-canvas and lazy-load architectural decisions must be made in Phase 1 because retrofitting them later is classified as HIGH recovery cost in PITFALLS.md
- Pipeline visualization (Phase 5) is sequenced after both the component library (Phase 2) and motion layer (Phase 3) are complete, because it uses both; it does not depend on the page upgrades (Phase 4/6) and can run in parallel with them
- Hero 3D scene (Phase 6) follows Pipeline (Phase 5) because R3F patterns are established there — reusing learned patterns reduces risk
- Anti-features (3D charts, parallax, continuous glitch) are explicitly excluded at every phase boundary

### Research Flags

Phases needing deeper planning (consider `/gsd:research-phase`):
- **Phase 5 (Pipeline Visualization):** The 2D→3D upgrade path for pipeline particles is novel. The elkjs async Web Worker integration with React Flow requires careful debouncing. The `usePipelineFlow()` data contract design determines whether both 2D and 3D views can coexist cleanly.
- **Phase 6 (Hero 3D Scene):** GPU tier detection heuristics for `useGPUTier` need validation across real hardware. SelectiveBloom layer mask setup with postprocessing v3 may have edge cases.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1 (CSS Foundation):** Pure CSS variable overrides + Tailwind 4 theme — zero uncertainty
- **Phase 2 (Component Library):** shadcn/ui + augmented-ui + Motion v12 all have extensive official documentation
- **Phase 3 (Ambient Effects):** tsParticles + AnimatePresence patterns are completely standard
- **Phase 4 (Page Upgrades):** Recharts restyling via custom themes is well-documented; Motion stagger is standard

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against official npm + official docs via Context7. React 19 compatibility confirmed for every primary dependency. Version compatibility matrix validated. |
| Features | MEDIUM-HIGH | Table stakes derived from extensive visual reference analysis (Dribbble, Behance, game UI critiques). Differentiators validated against Shopify BFCM first-party engineering writeups. Anti-features backed by UX research. Some UX impact metrics (session duration +65%) from single source. |
| Architecture | HIGH | Architecture derived directly from existing codebase analysis + official R3F/React Flow docs. Patterns verified against Context7 library documentation. Data flow designed around existing API shapes confirmed in CLAUDE.md. |
| Pitfalls | HIGH | All 8 critical pitfalls sourced from official library docs (R3F pitfalls page, React Flow performance docs) and post-mortems. Recovery cost estimates conservative. WebGL context limit numbers browser-verified. |

**Overall confidence:** HIGH

### Gaps to Address

- **Theatre.js React 19 compatibility:** Pre-1.0, unconfirmed. Deferred to Phase 7+ or post-launch. If cinematic camera sequences become needed, validate Theatre.js 0.7.2 against React 19.2 in a throwaway branch before committing.
- **GPU tier thresholds:** The `useGPUTier` heuristic (Intel/Mali/Adreno = medium, else high) is a rough approximation. Real-device testing on Intel UHD 630, M-series MacBook Air, and 3-year-old Android required before Phase 6 ships.
- **WebSocket pipeline_progress event schema:** CLAUDE.md notes the `/api/pipeline/run` background task is a stub (logs only, does not call PipelineOrchestrator). The `usePipelineFlow()` hook design depends on the real event schema. Validate the WS event structure before Phase 5 implementation begins, or build against mock events with a documented interface.
- **augmented-ui + shadcn/ui interaction:** PITFALLS.md flags that augmented-ui clip-paths can conflict with shadcn border-radius and overflow styles. Must test each cyber component combination explicitly before Phase 2 is marked complete.

## Sources

### Primary (HIGH confidence)
- Context7 `/pmndrs/react-three-fiber` — React 19 compatibility, canvas architecture, useFrame patterns, performance pitfalls
- Context7 `/pmndrs/drei` — helper library overview, shader materials, Stars, Float, Grid helpers
- Context7 `/pmndrs/react-postprocessing` — Bloom, ChromaticAberration, EffectComposer, SelectiveBloom
- Context7 `/websites/reactflow_dev` — custom nodes, edge types, performance, elkjs integration
- Context7 `/websites/motion_dev_react` — React 19 compatibility, AnimatePresence, layout animations, motion/three limitation
- Context7 `/llmstxt/gsap_llms_txt` — useGSAP hook, React integration, GSAP timeline patterns
- Context7 `/websites/ui_shadcn` — Vite installation, CSS variable theming, Tailwind 4 setup
- Official npm: three@0.183.1, @react-three/fiber@9.5.0, @react-three/drei@10.7.7, @xyflow/react@12.10.1, motion@12.34.3, gsap@3.14.2
- [R3F Performance Pitfalls (official)](https://r3f.docs.pmnd.rs/advanced/pitfalls) — all 8 critical pitfalls validated
- [React Flow Performance (official)](https://reactflow.dev/learn/advanced-use/performance) — edge animation bottleneck confirmed
- [Motion for R3F docs](https://motion.dev/docs/react-three-fiber) — React 18-only limitation confirmed in official docs

### Secondary (MEDIUM confidence)
- [Shopify BFCM Engineering Blog](https://shopify.engineering/how-we-built-shopifys-bfcm-2023-globe) — R3F particle flow techniques, GPU instancing
- [augmented-ui v2 Documentation](https://augmented-ui.com/docs/) — HUD clip-path system
- [Magic UI Components](https://magicui.design/docs/components) — BorderBeam, AnimatedList, TypingAnimation
- [CYBERCORE CSS docs](https://sebyx07.github.io/cybercore-css/) — scanlines, glitch, noise components
- [excited.agency Dashboard UX Research](https://excited.agency/blog/dashboard-ux-design) — anti-patterns for data-heavy dark dashboards
- Existing Syntrix codebase (CLAUDE.md, direct file reads) — confirmed existing architecture, API shape, known stubs

### Tertiary (LOW confidence, inspiration only)
- Dribbble/Behance cyberpunk UI galleries — visual reference for table stakes feature identification
- Cyberpunk 2077 HUD analysis — anti-pattern identification (overuse of glitch effects)
- Theatre.js releases — deferred due to pre-1.0 status and unconfirmed React 19 compat

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*
