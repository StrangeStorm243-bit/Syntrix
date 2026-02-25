# Stack Research

**Domain:** Cyberpunk immersive 3D dashboard (React SPA upgrade)
**Researched:** 2026-02-24
**Confidence:** HIGH

## Existing Stack (Do Not Change)

These are already installed and must remain. No re-evaluation needed.

| Technology | Version | Purpose |
|------------|---------|---------|
| React | ^19.2.0 | UI framework |
| Vite | ^7.3.1 | Build tool |
| TypeScript | ~5.9.3 | Type safety |
| Tailwind CSS | ^4.2.1 | Utility-first CSS |
| TanStack Query | ^5.90.21 | Server state management |
| Recharts | ^3.7.0 | Charts (will be restyled, not replaced) |
| React Router DOM | ^7.13.1 | Client routing |
| Lucide React | ^0.575.0 | Icons |
| clsx | ^2.1.1 | Class name utility |
| Vitest | ^4.0.18 | Testing |

## Recommended Stack

### 3D Rendering — React Three Fiber Ecosystem

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| three | ^0.183.1 | 3D engine | Industry standard WebGL/WebGPU engine. R183 is current as of Feb 2026. WebGPU-ready since r171. | HIGH |
| @react-three/fiber | ^9.5.0 | React renderer for Three.js | v9 pairs with React 19 natively (confirmed in docs). Declarative 3D that fits existing React component model. The only production-grade React 3D renderer. | HIGH |
| @react-three/drei | ^10.7.7 | R3F helper library | 570+ snippets of ready-made abstractions (shaders, controls, text, materials). Eliminates boilerplate for common 3D patterns. Compatible with R3F v9. | HIGH |
| @react-three/postprocessing | ^3.0.4 | Post-processing effects | Bloom, chromatic aberration, vignette, noise — essential for the neon glow cyberpunk aesthetic. Wraps pmndrs/postprocessing for R3F. | HIGH |
| @types/three | latest | TypeScript types for Three.js | Required for TypeScript projects using Three.js directly. Version should match three.js version. | HIGH |

**Key finding:** R3F v9 is explicitly designed for React 19. The docs state: "@react-three/fiber@9 pairs with react@19" and is "compatible with all versions of React between 19.0 and 19.2." This is a perfect match for our React ^19.2.0 setup.

### Node Graph — Pipeline Visualization

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| @xyflow/react | ^12.10.1 | Node-based DAG graph | Purpose-built for directed node graphs. Supports custom node/edge rendering, which we need for cyberpunk-styled pipeline stages. 24k+ stars, actively maintained (updated 5 days ago). Built-in dark mode via `colorMode` prop. | HIGH |
| elkjs | ^0.11.0 | Automatic DAG layout | ELK's layered algorithm is specifically designed for directed graphs with ports — exactly what a pipeline DAG needs. Used in React Flow's official examples. Computes positions only (no rendering), so it pairs cleanly with xyflow. | HIGH |

**Why @xyflow/react over react-force-graph:** The pipeline (collect -> judge -> score -> draft -> send) is a directed acyclic graph, not a force-directed network. @xyflow/react handles DAGs natively with defined node positions and directed edges. react-force-graph uses physics simulation which makes node positions unpredictable — wrong tool for a pipeline. react-force-graph is appropriate for exploratory network visualization (social graphs, knowledge graphs), not pipeline flow.

### Animation — UI Layer

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| motion | ^12.34.3 | React UI animations | Formerly Framer Motion. 18M+ monthly npm downloads. React 19 compatible (confirmed). Import from `motion/react`. Best-in-class for layout animations, gestures, page transitions, micro-interactions. | HIGH |
| gsap | ^3.14.2 | Complex sequenced timelines | GSAP is the gold standard for complex, multi-element, sequenced animations. Now 100% FREE including all bonus plugins (SplitText, MorphSVG, etc). ScrollTrigger for scroll-driven effects. | HIGH |
| @gsap/react | ^2.1.2 | GSAP React integration | Provides `useGSAP()` hook — drop-in replacement for `useEffect` that automatically handles animation cleanup. Prevents memory leaks and strict mode issues. | HIGH |

**Division of labor:** Use Motion for declarative component animations (enter/exit, hover, layout shifts, page transitions). Use GSAP for complex timelines where you need precise sequencing across multiple elements (e.g., boot-up sequences, staggered card reveals, synchronized multi-element choreography).

**CRITICAL FINDING — Motion for R3F is React 18 only:** The Motion docs explicitly state that "Motion for React Three Fiber is currently only compatible with React 18." Since we use React 19, we CANNOT use `motion/three`. For animating 3D objects, use Three.js native animation (useFrame hook in R3F), GSAP with `useGSAP()`, or Theatre.js. This does NOT affect Motion for 2D React UI — that works fine with React 19.

### Animation — 3D/Cinematic (Optional)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| @theatre/core | ^0.7.2 | Cinematic 3D animation editor | Visual timeline editor for camera paths and complex 3D sequences. 11k stars. Best tool for "hero section camera fly-throughs" where you need precise artistic control. | MEDIUM |
| @theatre/studio | ^0.7.2 | Theatre.js visual editor (dev only) | Studio UI for designing animations visually. Dev-time tool — strip from production builds. | MEDIUM |
| @theatre/react | ^0.7.2 | Theatre.js React bindings | React hooks for Theatre.js integration. | MEDIUM |

**Confidence is MEDIUM because:** Theatre.js is still pre-1.0 (0.7.2, published 2 years ago with 1.0 "around the corner"). It works with R3F but React 19 compatibility is unconfirmed. Recommend: defer Theatre.js to a later phase and verify compatibility first. GSAP + R3F `useFrame` can cover most 3D animation needs without Theatre.js.

### UI Components — Foundation

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| shadcn/ui | latest (CLI: `npx shadcn@latest`) | Component foundation | Copy-paste model gives full source code ownership. CSS variable theming is perfect for cyberpunk customization — just override the oklch values with our neon palette. Supports Vite + React + Tailwind 4 natively. Not an npm dependency — code lives in your project. | HIGH |
| tailwind-animate / tw-animate-css | latest | Tailwind animation utilities | Required by shadcn/ui for enter/exit animations. Lightweight CSS-only approach. | HIGH |

**shadcn/ui theming approach:** Override the CSS variables in `:root` / `.dark` with our cyberpunk palette. shadcn uses oklch color space which supports the full gamut needed for vibrant neons. Map `--primary` to hot pink, `--secondary` to orange, `--accent` to gold, etc.

### UI Components — Cyberpunk Effects

| Technology | Version | Purpose | When to Use | Confidence |
|------------|---------|---------|-------------|------------|
| augmented-ui | ^2.0.0 | HUD clip-path borders | Card borders, panel frames, button shapes. Pure CSS — 150+ custom properties for clip-path augmentations. Import the CSS file, add `data-augmented-ui` attributes. Zero JS overhead. | HIGH |
| cybercore-css | ^0.7.0 | Scanlines, glitch, terminal effects | Overlay effects on cards/sections. Pure CSS, framework-agnostic, modular SCSS imports. 14 components, 6 effects (glitch, neon border, scanlines, noise, datastream, text glow). | MEDIUM |
| Magic UI | copy-paste | Animated UI components | BorderBeam, Particles, ShineBorder, SparklesText, AnimatedGridPattern. Same copy-paste model as shadcn/ui. 19k stars. Built with Tailwind + Motion. Cherry-pick individual components — no bulk install. | HIGH |

**Why NOT Aceternity UI as primary:** Aceternity UI components are built for Next.js and some have Next.js-specific imports (e.g., `next/image`, `next/link`). They can be adapted for Vite+React but require manual conversion. Magic UI is framework-agnostic by design. **Use Aceternity as a secondary source** — cherry-pick specific effects (BackgroundBeams, SpotlightCard) and manually adapt them.

**Why NOT Cosmic UI:** Multiple packages exist under this name with conflicting APIs. The TailwindCSS-based Cosmic UI (519 stars) is promising but immature. @stargazers-stella/cosmic-ui is a different library entirely. Confusion risk is high. Cherry-pick specific effects via CSS/GLSL rather than adopting a young framework.

**Why NOT ARWES:** Still in alpha (1.0.0-next.25020502), explicitly does NOT work with React strict mode, and only supports React 18. Since we use React 19, ARWES is not viable. Use it as design inspiration only, not as a dependency.

### Particles

| Technology | Version | Purpose | When to Use | Confidence |
|------------|---------|---------|-------------|------------|
| @tsparticles/react | ^3.0.0 | 2D particle backgrounds | Ambient floating particles on dashboard pages. Canvas-based, configurable presets. Use for pages that don't have a full R3F scene. | MEDIUM |
| Custom GLSL in R3F | n/a | 3D integrated particles | Particle flow between pipeline nodes, ambient 3D particles. Use drei's `shaderMaterial` helper for custom GLSL. More performant than tsParticles when already in a Three.js scene. | HIGH |

**Division of labor:** Use tsParticles for lightweight 2D ambient particles on non-3D pages. Use custom GLSL shaders within R3F for 3D particle effects (pipeline flow, hero background). Don't layer tsParticles on top of an R3F canvas — that's two rendering contexts competing.

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| leva | latest | Dev-time 3D controls panel | Tweak R3F scene parameters (bloom intensity, camera position, particle count) during development. Strip from production. | HIGH |
| r3f-perf | latest | R3F performance monitor | FPS, draw calls, memory monitoring during development. Essential for ensuring 60fps target. Dev-only. | HIGH |
| @react-three/a11y | latest | 3D accessibility | Screen reader support for interactive 3D elements. | MEDIUM |

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| @xyflow/react | react-force-graph-3d v1.29.1 | Pipeline is a DAG, not a force graph. Force layout makes positions unpredictable. xyflow gives deterministic, designed layouts. |
| Motion v12 | react-spring | Motion has wider adoption (18M/mo vs ~2M/mo), better React 19 support, and more features (layout animations, gestures). react-spring's maintenance has been inconsistent. |
| Motion v12 | @react-spring/web | Same as above. Motion is the community standard for React animation in 2025/2026. |
| GSAP | anime.js | GSAP has better timeline sequencing, more plugins (ScrollTrigger, SplitText now free), and the @gsap/react hook. anime.js v4 rewrite broke many patterns. |
| shadcn/ui | Chakra UI / MUI | shadcn gives source code ownership — critical for deep cyberpunk theming. Chakra/MUI fight you when overriding design tokens this aggressively. |
| augmented-ui | Custom clip-paths | augmented-ui has 150+ tested clip-path combinations. Writing custom clip-paths for HUD borders is error-prone and time-consuming. Use the library. |
| Custom GLSL + R3F | tsParticles for 3D scenes | Don't run two rendering contexts (canvas + WebGL) on the same view. When R3F is active, particle effects should be GLSL shaders inside the Three.js scene. |
| GSAP for 3D animation | Motion for R3F | Motion's R3F integration (motion/three) is React 18 only. Cannot use with our React 19 setup. GSAP + useFrame covers the same ground. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| ARWES (@arwes/react) | Alpha quality, no React strict mode support, React 18 only. Not viable for React 19 production app. | Use as design inspiration. Build effects with augmented-ui + cybercore-css + custom CSS. |
| motion/three (Motion for R3F) | Explicitly React 18 only. Will break with React 19. | GSAP + @gsap/react for 3D animations, or R3F's useFrame for per-frame updates. |
| framer-motion (legacy package) | Deprecated in favor of `motion`. Legacy package will stop receiving updates. | Import from `motion/react` instead of `framer-motion`. |
| react-three-fiber (unscoped) | Deprecated 5+ years ago. Last version 6.0.13. | Use `@react-three/fiber` (scoped package). |
| drei (unscoped) | Deprecated. | Use `@react-three/drei` (scoped package). |
| react-force-graph for pipeline | Wrong algorithm for DAGs. Force-directed layout is for network graphs. | @xyflow/react + elkjs for deterministic pipeline layouts. |
| Cosmic UI (any variant) | Multiple conflicting packages under same name. Immature (519 stars). API confusion risk. | Cherry-pick effects from Magic UI or write custom CSS/GLSL. |
| Theatre.js in Phase 1 | Pre-1.0, React 19 compatibility unconfirmed, complex setup. | Defer to later phase after core 3D infrastructure proves stable. Validate React 19 compat first. |
| tsParticles ON TOP of R3F canvas | Two rendering contexts = performance hit + z-index battles. | Use GLSL particle shaders inside R3F when a 3D scene is active. |

## Version Compatibility Matrix

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| @react-three/fiber@^9.5.0 | react@^19.2.0, three@^0.183.1 | R3F v9 = React 19. Confirmed compatible with React 19.0 through 19.2. |
| @react-three/drei@^10.7.7 | @react-three/fiber@^9.x | Drei v10 pairs with R3F v9. |
| @react-three/postprocessing@^3.0.4 | @react-three/fiber@^9.x, three@^0.183.1 | Wraps pmndrs/postprocessing. |
| motion@^12.34.3 | react@^19.2.0 | Import from `motion/react`. React 18.2+ required. |
| motion/three | react@18.x ONLY | DO NOT USE with React 19. |
| gsap@^3.14.2 | Any (framework-agnostic) | Core GSAP has no React dependency. |
| @gsap/react@^2.1.2 | react@^18.x or ^19.x | useGSAP hook is a standard React hook. |
| @xyflow/react@^12.10.1 | react@^18.x or ^19.x | Standard React component library. Built-in dark mode. |
| elkjs@^0.11.0 | Any (pure computation) | No UI dependency. Runs in web worker. |
| shadcn/ui | react@^19.x, tailwindcss@^4.x | Not an npm dep. CLI generates source code. Requires Tailwind 4 (we have it). |
| augmented-ui@^2.0.0 | Any (pure CSS) | No JS dependency. Import CSS file. |
| cybercore-css@^0.7.0 | Any (pure CSS/SCSS) | No JS dependency. Framework-agnostic. |
| @tsparticles/react@^3.0.0 | react@^18.x or ^19.x | React wrapper for tsParticles engine. |
| @theatre/core@^0.7.2 | Unknown for React 19 | UNCONFIRMED. Only verified for React 18. Defer and test. |

## Installation

```bash
# ---- Run from dashboard/ directory ----

# 3D Rendering (core)
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing
npm install -D @types/three

# Node Graph (pipeline visualization)
npm install @xyflow/react elkjs

# Animation (UI layer)
npm install motion gsap @gsap/react

# Particles (ambient 2D backgrounds)
npm install @tsparticles/react @tsparticles/slim

# UI Effects (CSS-only, import stylesheets)
npm install augmented-ui cybercore-css

# shadcn/ui (run init, then add components as needed)
npx shadcn@latest init
# Then cherry-pick: npx shadcn@latest add button card dialog dropdown-menu

# Dev tools (strip from production)
npm install -D leva r3f-perf
```

**Bundle size strategy:** Lazy-load 3D dependencies with `React.lazy()` and `Suspense`. The R3F ecosystem is heavy (~500KB+ for three.js alone). Pages without 3D scenes should NOT load Three.js. Use dynamic imports:

```typescript
const PipelineGraph = React.lazy(() => import('./components/PipelineGraph'))
const HeroScene = React.lazy(() => import('./components/HeroScene'))
```

## Stack Patterns by Context

**If the page has a full 3D scene (Dashboard hero, Pipeline view):**
- Use R3F + drei + postprocessing for rendering
- Use GSAP or R3F useFrame for 3D animation (NOT motion/three)
- Use GLSL shaders for particle effects inside the scene
- Bloom postprocessing for neon glow

**If the page is primarily 2D with effects (Leads, Queue, Analytics):**
- Use Motion for enter/exit, hover, layout animations
- Use GSAP for complex multi-element timelines
- Use tsParticles for ambient particle background
- Use augmented-ui for HUD card borders
- Use cybercore-css for scanline/glitch overlays

**If building a reusable UI component (cards, buttons, inputs):**
- Start with shadcn/ui base component
- Override CSS variables for cyberpunk palette
- Add augmented-ui clip-path borders via data attributes
- Add Motion hover/tap animations
- Cherry-pick Magic UI effects (BorderBeam, ShineBorder) as needed

## Color Palette (CSS Custom Properties)

These values override shadcn/ui's default CSS variables:

```css
:root {
  /* Cyberpunk warm palette */
  --bg-void: #0a0608;
  --bg-panel: #12090e;
  --neon-primary: #ff1493;     /* deep hot pink */
  --neon-secondary: #ff6b35;   /* hot orange */
  --neon-accent: #ffd700;      /* gold */
  --text-primary: #ffe0ec;     /* warm white, pink tint */
  --text-data: #ff9955;        /* orange data values */

  /* Map to shadcn/ui variables (convert to oklch for consistency) */
  --background: oklch(0.04 0.02 350);     /* ~#0a0608 */
  --foreground: oklch(0.93 0.02 350);     /* ~#ffe0ec */
  --card: oklch(0.08 0.03 340);           /* ~#12090e */
  --primary: oklch(0.65 0.28 340);        /* ~#ff1493 */
  --secondary: oklch(0.65 0.20 40);       /* ~#ff6b35 */
  --accent: oklch(0.85 0.18 90);          /* ~#ffd700 */
}
```

## Sources

### Context7 (HIGH confidence)
- `/pmndrs/react-three-fiber` — Installation, React 19 compatibility confirmation (v9 = React 19)
- `/websites/reactflow_dev` — Custom nodes, edge types, React Flow API
- `/websites/motion_dev_react` — Installation, React 19 compatibility, upgrade guide from framer-motion
- `/pmndrs/drei` — Installation, shader materials, helpers overview
- `/llmstxt/gsap_llms_txt` — useGSAP hook, React integration patterns
- `/websites/ui_shadcn` — Vite installation, CSS variable theming, dark mode setup

### Official Docs / npm (HIGH confidence)
- [three@0.183.1 on npm](https://www.npmjs.com/package/three) — Latest Three.js version
- [@react-three/fiber@9.5.0 on npm](https://www.npmjs.com/package/@react-three/fiber) — R3F latest
- [@react-three/drei@10.7.7 on npm](https://www.npmjs.com/package/@react-three/drei) — Drei latest
- [@react-three/postprocessing@3.0.4 on npm](https://www.npmjs.com/package/@react-three/postprocessing) — Postprocessing latest
- [@xyflow/react@12.10.1 on npm](https://www.npmjs.com/package/@xyflow/react) — React Flow latest
- [elkjs@0.11.0 on npm](https://www.npmjs.com/package/elkjs) — ELK layout engine
- [motion@12.34.3 on npm](https://www.npmjs.com/package/framer-motion) — Motion latest (framer-motion page redirects)
- [gsap@3.14.2 on npm](https://www.npmjs.com/package/gsap) — GSAP latest
- [@gsap/react@2.1.2 on npm](https://www.npmjs.com/package/@gsap/react) — GSAP React hook
- [augmented-ui@2.0.0 on npm](https://www.npmjs.com/package/augmented-ui) — HUD clip-path borders
- [shadcn/ui Vite install guide](https://ui.shadcn.com/docs/installation/vite) — Official Vite setup
- [Motion for R3F docs](https://motion.dev/docs/react-three-fiber) — React 18 only limitation confirmed

### WebSearch (MEDIUM confidence, verified with official sources)
- [Motion changelog](https://motion.dev/changelog) — Version history
- [React Flow 12 release blog](https://xyflow.com/blog/react-flow-12-release) — v12 feature overview
- [GSAP free announcement](https://gsap.com/docs/v3/Installation/) — All plugins now free
- [Magic UI docs](https://magicui.design/docs/installation) — Copy-paste install model
- [ARWES docs](https://arwes.dev/docs) — Alpha status, React strict mode incompatibility
- [CYBERCORE CSS](https://sebyx07.github.io/cybercore-css/) — Pure CSS cyberpunk effects
- [Aceternity UI](https://ui.aceternity.com) — Next.js-oriented, adaptation needed for Vite

### WebSearch (LOW confidence, design inspiration only)
- [Cosmic UI](https://github.com/Raw-Fun-Gaming/cosmic-ui-lite) — Design reference, not recommended as dependency
- [Theatre.js releases](https://www.theatrejs.com/docs/latest/releases) — Pre-1.0, React 19 unconfirmed

---
*Stack research for: Cyberpunk immersive 3D dashboard*
*Researched: 2026-02-24*
