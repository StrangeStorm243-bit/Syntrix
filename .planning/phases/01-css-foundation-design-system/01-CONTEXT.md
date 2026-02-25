# Phase 1: CSS Foundation & Design System - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the cyberpunk visual identity via CSS custom properties, initialize shadcn/ui with cyberpunk oklch theme, create CyberpunkLayout wrapper that replaces DashboardLayout, and set architectural guardrails for 3D (lazy-load boundaries, single-canvas strategy, ref-based animation convention). All 6 existing pages must render through the new layout with no functional regression.

</domain>

<decisions>
## Implementation Decisions

### Color Palette
- Cyberpunk warm palette: dark void bg (#0a0608), hot pink (#ff1493), orange (#ff6b35), gold (#ffd700)
- CSS custom properties using oklch color space for perceptual uniformity
- All colors exposed as `--cyber-*` CSS vars for downstream components

### Glassmorphism
- Frosted glass utility classes: `backdrop-blur`, translucent backgrounds, subtle neon border glow
- Reusable as utility classes (not component-locked) so any element can be glass

### Neon Glow
- Box-shadow glow states on hover/focus for interactive elements (buttons, links, inputs)
- Glow color derived from the cyberpunk palette (pink/orange primary glows)

### Scanline / CRT Effect
- Subtle CRT overlay texture applied across panels
- Repeating gradient scanline pattern, low opacity for readability

### Typography
- Monospace HUD typography for data values (JetBrains Mono or Orbitron)
- Standard body font retained for readability of prose content

### shadcn/ui
- Initialize shadcn/ui CLI with cyberpunk oklch theme variables
- `components.json` configured, theme tokens set

### Layout
- CyberpunkLayout wrapper replaces existing DashboardLayout
- All 6 existing pages (Dashboard, Leads, Queue, Analytics, Experiments, Settings) nest inside
- No visual regression in functionality — progressive enhancement

### 3D Architectural Guardrails
- `lazy-3d.ts` utility for lazy-loading future 3D imports (React.lazy + Suspense patterns)
- Single-canvas strategy documented (one persistent Canvas at layout level)
- `useRef` animation convention documented (never setState inside useFrame)

### Claude's Discretion
- Exact oklch values derived from the hex palette
- Scanline animation speed and density
- Glassmorphism blur radius and opacity values
- Specific shadcn/ui component variants to override
- CSS custom property naming convention details

</decisions>

<specifics>
## Specific Ideas

- Progressive upgrade approach — not a full rebuild. Existing pages should still work throughout
- Cyberpunk warm palette deliberately chosen (pink/orange/gold) rather than cool blue/cyan
- R3F v9 for 3D, @xyflow for pipeline DAG, Motion v12 for 2D animations, GSAP for timelines (tech stack locked)
- shadcn/ui + Magic UI for component primitives
- 4 parallel terminals execution strategy — Phase 1 is the shared foundation all terminals depend on

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-css-foundation-design-system*
*Context gathered: 2026-02-24*
