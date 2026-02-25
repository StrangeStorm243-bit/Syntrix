# Syntrix Dashboard — Cyberpunk Immersive UI Overhaul

## What This Is

A progressive redesign of the Syntrix web dashboard from a functional-but-static React SPA into a futuristic, immersive cyberpunk command center. The dashboard is the primary interface for social lead intelligence — monitoring X/Twitter for high-intent leads, reviewing AI judgments, approving reply drafts, and analyzing outreach performance. The redesign prioritizes a balanced experience: stunning 3D visuals and animations that serve the data, not obscure it.

## Core Value

The pipeline live view — users must see tweets flowing through collect -> judge -> score -> draft as animated particles in a 3D node graph, making the invisible pipeline tangible and the product feel alive.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 3D pipeline node graph with animated particle flow between stages
- [ ] Cyberpunk warm color system (dark base, hot pink/orange/gold neon accents)
- [ ] Immersive dashboard overview with 3D hero background and animated metric cards
- [ ] shadcn/ui component foundation with cyberpunk theme
- [ ] Motion/animation layer for page transitions, micro-interactions, hover effects
- [ ] Real-time WebSocket integration showing live pipeline activity
- [ ] Progressive upgrade path — existing pages keep working while new UI layers on
- [ ] Neon-styled Recharts with warm gradient fills and glassmorphism tooltips
- [ ] HUD-style card borders with augmented-ui clip-paths
- [ ] Ambient particle background effects
- [ ] Post-processing effects (bloom, chromatic aberration) on 3D scenes
- [ ] Responsive design that degrades gracefully on mobile (2D fallback)

### Out of Scope

- Full rebuild from scratch — we're upgrading progressively, page by page
- Light mode / theme switcher — cyberpunk is always dark
- Mobile-first design — desktop-first, mobile-responsive as secondary
- Remotion video export — bookmarked for future, not this milestone
- New backend API endpoints — frontend-only changes using existing API
- New dashboard pages — enhance existing 6 pages, don't add new ones
- E2E testing with Playwright/Cypress — unit tests only for now

## Context

**Current state:** The dashboard is ~1,766 lines of React 19 + TypeScript + Vite 7 + Tailwind 4 + TanStack Query 5 + Recharts 3. It has 6 pages (Dashboard, Leads, Queue, Analytics, Experiments, Settings), 11 components, 6 data hooks, and a WebSocket infrastructure that isn't connected to the UI yet. Visually it's clean but completely static — no animations, no depth, no glow effects.

**Target aesthetic:** Cyberpunk warm — near-black backgrounds with hot pink, orange, and gold neon accents. Full 3D scenes using React Three Fiber. Node graph pipeline visualization with glowing particles flowing between stages. Glassmorphism panels. Scanline overlays. HUD-style angled borders. Ambient floating particles. Bloom post-processing for neon glow. The feel of a sci-fi command center that's also genuinely functional for daily lead management.

**Color palette:**
- `--bg-void: #0a0608` (near-black, warm undertone)
- `--bg-panel: #12090e` (dark panel)
- `--neon-primary: #ff1493` (deep hot pink)
- `--neon-secondary: #ff6b35` (hot orange)
- `--neon-accent: #ffd700` (gold)
- `--text-primary: #ffe0ec` (warm white, pink tint)
- `--text-data: #ff9955` (orange data values)

**Key libraries to integrate:**
- React Three Fiber v9 + drei v10 + @react-three/postprocessing (3D)
- @xyflow/react v12 + elkjs (pipeline node graph)
- shadcn/ui with cyberpunk CSS variables (component foundation)
- Magic UI + Aceternity UI cherry-picks (animated components)
- Motion v12 (micro-interactions, page transitions)
- GSAP (complex sequenced timelines)
- tsParticles (ambient particle backgrounds)
- augmented-ui (HUD clip-path borders)
- CYBERCORE CSS (scanlines, glitch, terminal effects)

**Inspiration sources:**
- Shopify BFCM Live Globe (R3F particle flow technique)
- ARWES sci-fi framework (design patterns)
- Cosmic UI (holographic effects, matching stack)
- 21st.dev Animated Shader Background (GLSL aurora)
- Framer "Future" / "Dune" templates (layout reference)

## Constraints

- **Stack**: Must remain React 19 + Vite 7 + TypeScript + Tailwind 4 — no framework switch
- **Progressive**: Existing pages must continue working during upgrade — no big-bang rewrite
- **Performance**: 3D scenes must maintain 60fps on modern hardware; degrade gracefully on low-end
- **Bundle size**: Lazy-load Three.js and heavy 3D dependencies — don't bloat initial page load
- **API**: Frontend-only changes — no backend modifications required
- **Existing tests**: Current 4 test files must continue to pass throughout

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React Three Fiber over raw Three.js | Declarative, React-native, hooks-based — fits existing React 19 codebase | — Pending |
| @xyflow/react over react-force-graph for pipeline | Pipeline is a DAG (directed), not force-directed — xyflow handles DAGs natively with elkjs | — Pending |
| shadcn/ui as component foundation | Copy-paste model = full control, CSS variable theming = easy cyberpunk customization | — Pending |
| Motion v12 over react-spring | React 19 confirmed compatible, lighter bundle, better community adoption | — Pending |
| Magic UI as primary animated component source | 19k stars, shadcn-style copy-paste, Tailwind-native, most active community | — Pending |
| Progressive upgrade over full rebuild | Lower risk, faster to show progress, existing functionality preserved | — Pending |
| Desktop-first responsive approach | Primary use case is desktop command center; mobile is secondary | — Pending |

---
*Last updated: 2026-02-24 after initialization*
