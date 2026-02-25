# Requirements: Syntrix Cyberpunk Dashboard

**Defined:** 2026-02-24
**Core Value:** Users see tweets flowing through the pipeline as animated particles in a 3D node graph, making the invisible pipeline tangible and the product feel alive.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Design System

- [ ] **DS-01**: Dashboard uses cyberpunk warm color palette (dark void bg #0a0608, hot pink #ff1493, orange #ff6b35, gold #ffd700) via CSS custom properties
- [ ] **DS-02**: All panels use glassmorphism styling (backdrop-blur, translucent bg, subtle neon border glow)
- [ ] **DS-03**: Interactive elements have neon glow states on hover/focus via box-shadow
- [ ] **DS-04**: Scanline/noise overlay applied as subtle CRT effect across panels
- [ ] **DS-05**: Data values use monospace typography (JetBrains Mono or Orbitron) for HUD readability
- [ ] **DS-06**: shadcn/ui initialized with cyberpunk CSS variable theme (oklch color space)
- [ ] **DS-07**: CyberpunkLayout wrapper replaces existing DashboardLayout with no visual regression

### Component Library

- [ ] **CL-01**: GlassCard component with glassmorphism styling and optional augmented-ui clip-path borders
- [ ] **CL-02**: NeonMetricCard component with animated number counter and glow effect
- [ ] **CL-03**: NeonSidebar with active state glow indicators and hover animations
- [ ] **CL-04**: NeonBadge/NeonButton components with neon border and glow states
- [ ] **CL-05**: NeonTable component with hover row glow and neon header styling
- [ ] **CL-06**: NeonInput/NeonTooltip components for forms and data display
- [ ] **CL-07**: Motion v12 animation presets (enter/exit/stagger variants) shared across all components

### Ambient Effects

- [ ] **AE-01**: Floating particle background (tsParticles) in layout with device-adaptive particle count
- [ ] **AE-02**: Page transitions using Motion AnimatePresence on router (fade + slide)
- [ ] **AE-03**: Staggered mount animations on page load ("system initializing" feel)
- [ ] **AE-04**: prefers-reduced-motion respected — all animations disabled when OS setting is on
- [ ] **AE-05**: Scanlines component mountable as subtle overlay on any panel

### Dashboard Page

- [ ] **DP-01**: Dashboard overview uses NeonMetricCard grid with animated counters for all 4 stats
- [ ] **DP-02**: Conversion funnel chart restyled with neon gradient fills and glassmorphism tooltip
- [ ] **DP-03**: Chart theme system (chart-theme.ts) with shared neon gradient tokens for all Recharts

### Analytics Page

- [ ] **AP-01**: Score distribution bar chart restyled with cyberpunk neon gradients (pink→orange)
- [ ] **AP-02**: Conversion funnel chart with neon styling matching dashboard
- [ ] **AP-03**: Query performance table uses NeonTable with glow row highlights

### Pipeline Visualization

- [ ] **PV-01**: usePipelineFlow() adapter hook combining useStats() + useWebSocket() into PipelineFlowData shape
- [ ] **PV-02**: 2D pipeline DAG using @xyflow/react with custom neon StageNode components and elkjs auto-layout
- [ ] **PV-03**: Animated data edges showing flow direction with animateMotion SVG (not stroke-dasharray)
- [ ] **PV-04**: Real-time WebSocket events animate new items entering the pipeline flow
- [ ] **PV-05**: Pipeline Live page accessible from sidebar navigation
- [ ] **PV-06**: 3D pipeline scene using R3F with StageOrb geometry and particle flow between stages
- [ ] **PV-07**: Post-processing bloom effect on 3D pipeline making neon elements physically glow
- [ ] **PV-08**: 2D/3D toggle switch allowing user to choose preferred visualization mode

### 3D Hero Scene

- [ ] **HS-01**: 3D hero background scene (R3F Canvas) behind Dashboard content with abstract animated geometry
- [ ] **HS-02**: SelectiveBloom post-processing making hero elements glow without washing out UI text
- [ ] **HS-03**: useGPUTier hook with quality tiers (HIGH=full postprocessing, MEDIUM=no postprocessing, LOW=2D fallback)

### Remaining Pages

- [ ] **RP-01**: Leads page uses NeonTable with glow row highlights and cyberpunk filter badges
- [ ] **RP-02**: Queue page uses GlassCard-based DraftCards with neon approve/reject buttons
- [ ] **RP-03**: Experiments page uses NeonTable with status glow indicators
- [ ] **RP-04**: Settings page uses NeonInput components with cyberpunk form styling

### Performance & Polish

- [ ] **PP-01**: Three.js and all 3D dependencies lazy-loaded — initial bundle under 200KB
- [ ] **PP-02**: Single persistent Canvas at layout level (not per-page) to avoid WebGL context exhaustion
- [ ] **PP-03**: All R3F animations use useRef pattern (never setState inside useFrame)
- [ ] **PP-04**: GPU memory stable over 30-minute navigation sessions (useDisposable utility applied)
- [ ] **PP-05**: WCAG AA contrast verified on all text against cyberpunk backgrounds
- [ ] **PP-06**: "Performance Mode" toggle in Settings to disable 3D/particles for low-end devices
- [ ] **PP-07**: Existing 4 test files continue to pass throughout the upgrade

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Advanced 3D

- **A3D-01**: 3D particle flow replacing 2D @xyflow edges (R3F instanced particles, Shopify BFCM technique)
- **A3D-02**: Theatre.js cinematic camera animations for intro/onboarding sequence
- **A3D-03**: GSAP complex sequenced intro timelines for dashboard "boot up" animation

### Extended Features

- **EF-01**: Sound effects system (opt-in, contextual sounds on actions)
- **EF-02**: Responsive 2D mobile fallback for all 3D scenes
- **EF-03**: Animated beams between related elements (Magic UI AnimatedBeam)
- **EF-04**: Remotion video export for campaign performance report summaries

## Out of Scope

| Feature | Reason |
|---------|--------|
| Light mode / theme switcher | Doubles CSS work, undermines entire cyberpunk aesthetic |
| 3D perspective charts | Distorts data perception, universally condemned by data viz experts |
| Aggressive/continuous glitch effects | Eye strain, photosensitivity risk, accessibility violation |
| Auto-playing sound | Universally hated, violates accessibility guidelines |
| Parallax scrolling on data pages | Motion sickness, breaks scroll usability on data-heavy pages |
| Custom cursor | Accessibility violation, confuses users |
| New backend API endpoints | Frontend-only milestone — existing API sufficient |
| New dashboard pages beyond Pipeline Live | Enhance existing pages, keep scope controlled |
| E2E testing (Playwright/Cypress) | Unit tests only for this milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DS-01 | Phase 1 | Pending |
| DS-02 | Phase 1 | Pending |
| DS-03 | Phase 1 | Pending |
| DS-04 | Phase 1 | Pending |
| DS-05 | Phase 1 | Pending |
| DS-06 | Phase 1 | Pending |
| DS-07 | Phase 1 | Pending |
| CL-01 | Phase 2 | Pending |
| CL-02 | Phase 2 | Pending |
| CL-03 | Phase 2 | Pending |
| CL-04 | Phase 2 | Pending |
| CL-05 | Phase 2 | Pending |
| CL-06 | Phase 2 | Pending |
| CL-07 | Phase 2 | Pending |
| AE-01 | Phase 3 | Pending |
| AE-02 | Phase 3 | Pending |
| AE-03 | Phase 3 | Pending |
| AE-04 | Phase 3 | Pending |
| AE-05 | Phase 3 | Pending |
| DP-01 | Phase 4 | Pending |
| DP-02 | Phase 4 | Pending |
| DP-03 | Phase 4 | Pending |
| AP-01 | Phase 4 | Pending |
| AP-02 | Phase 4 | Pending |
| AP-03 | Phase 4 | Pending |
| PV-01 | Phase 5 | Pending |
| PV-02 | Phase 5 | Pending |
| PV-03 | Phase 5 | Pending |
| PV-04 | Phase 5 | Pending |
| PV-05 | Phase 5 | Pending |
| PV-06 | Phase 5 | Pending |
| PV-07 | Phase 5 | Pending |
| PV-08 | Phase 5 | Pending |
| HS-01 | Phase 6 | Pending |
| HS-02 | Phase 6 | Pending |
| HS-03 | Phase 6 | Pending |
| RP-01 | Phase 6 | Pending |
| RP-02 | Phase 6 | Pending |
| RP-03 | Phase 6 | Pending |
| RP-04 | Phase 6 | Pending |
| PP-01 | Phase 7 | Pending |
| PP-02 | Phase 7 | Pending |
| PP-03 | Phase 7 | Pending |
| PP-04 | Phase 7 | Pending |
| PP-05 | Phase 7 | Pending |
| PP-06 | Phase 7 | Pending |
| PP-07 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after initial definition*
