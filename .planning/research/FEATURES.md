# Feature Research: Cyberpunk Immersive Dashboard

**Domain:** Futuristic/cyberpunk data dashboard UI for social lead intelligence
**Researched:** 2026-02-24
**Confidence:** MEDIUM-HIGH (based on extensive Dribbble/Behance pattern analysis, framework docs, Shopify BFCM engineering writeups, and cross-referenced UX research)

## Feature Landscape

### Table Stakes (Must Have or It Doesn't Feel Cyberpunk)

Features the audience assumes exist when they hear "cyberpunk dashboard." Missing any of these and the product feels like a dark theme with colored accents, not a sci-fi command center.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Dark void background** (`#0a0608` range) | Every cyberpunk reference uses near-black as canvas. Without it, nothing else reads as cyberpunk. | LOW | CSS variable swap. Tailwind 4 `@theme` directive. Already partially dark (`bg-gray-950`), needs warmth shift. |
| **Neon accent color system** (hot pink / orange / gold) | Neon-on-dark is the single most defining visual signature of the genre. Cold blue alone reads "generic dark mode." | LOW | Define 3 neon CSS variables + text/data variants. Apply to borders, text highlights, chart fills. The warm palette (pink/orange/gold) is a deliberate departure from typical cold cyan/blue. |
| **Glassmorphism panels** (backdrop-blur + translucent bg + subtle border) | Every Dribbble/Behance cyberpunk dashboard uses frosted glass cards. It's the standard container treatment. | LOW | `backdrop-blur-md bg-[#12090e]/60 border border-white/5`. Replace current `bg-gray-800/50 border-gray-700`. |
| **Neon glow on interactive elements** (buttons, links, focused inputs) | Users expect hover/focus states to emit light. Static neon text without glow feels flat and lifeless. | LOW | `box-shadow` with neon color + `text-shadow`. CSS-only, no JS. Apply to buttons, sidebar active state, table row hover. |
| **Animated number counters** (metric cards count up on load) | Static numbers on a "futuristic" dashboard feels broken. Even basic count-up animation signals life. | LOW | Magic UI `NumberTicker` or Motion `animate` with `useInView`. Drop-in replacement for current `MetricCard` values. |
| **Neon-styled charts** (warm gradient fills, glow effects on data) | Current Recharts use cold blue/purple fills with gray tooltips. Must shift to warm neon palette with gradient fills. | MEDIUM | Custom Recharts theme: `linearGradient` fills (pink-to-orange), neon-colored axes, glassmorphism tooltip containers. Recharts supports `<defs>` gradients natively. |
| **Monospace / tech typography** (headers or data values) | HUD interfaces universally use monospace or geometric sans for data readability and genre signaling. | LOW | `font-mono` on data values + metric numbers. Keep body text in readable sans-serif. Use `JetBrains Mono` or `Space Mono` for data. |
| **Scanline / noise overlay** (subtle, not aggressive) | The CRT-monitor texture is cyberpunk's visual fingerprint. Without it, the interface reads as "clean modern dark" not "dystopian tech." | LOW | CSS-only repeating-linear-gradient (1-2px lines at 3-5% opacity). CYBERCORE CSS provides this. Single `::after` pseudo-element on layout wrapper. Zero performance cost. |
| **Animated page transitions** (fade, slide, or morph between routes) | Hard-cutting between pages on a "futuristic" dashboard breaks immersion. Even subtle fade-in signals polish. | MEDIUM | Motion `AnimatePresence` wrapping React Router `<Outlet>`. Stagger children on mount. Need `layout` prop for shared elements. |
| **Border beam / shine effects on cards** | Animated light traveling along card borders is ubiquitous in cyberpunk UI kits. It signals "active" and "powered." | LOW | Magic UI `BorderBeam` component. CSS-only, copy-paste. Apply to primary metric cards and panel headers. |
| **Loading skeleton with glow pulse** | Standard gray skeleton doesn't fit. Cyberpunk loading states should pulse with neon color, like circuits powering on. | LOW | Replace current `LoadingSpinner` with neon-pulsing skeleton shapes. CSS `@keyframes` with neon color shimmer. |

### Differentiators (Competitive Advantage / Wow Factor)

Features that make users stop and say "I've never seen a dashboard do this." These separate a themed dashboard from a genuinely immersive experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **3D pipeline node graph with particle flow** | **The core value.** Tweets flowing as glowing particles through collect->judge->score->draft stages. Makes the invisible pipeline tangible. No competitor dashboard visualizes ML pipelines as animated 3D flows. | HIGH | @xyflow/react for DAG layout + elkjs for auto-positioning. Custom animated edges with SVG particle trails. Alternatively, full R3F scene with instanced particles on Bezier curves (Shopify BFCM technique). Start with 2D xyflow, upgrade to R3F later. |
| **3D hero background scene** (ambient, behind dashboard content) | A subtle 3D environment (floating particles, grid plane, volumetric light) behind transparent panels creates depth no CSS-only dashboard can match. Shopify BFCM and Active Theory V6 both use this. | HIGH | React Three Fiber `<Canvas>` as fixed background. drei helpers: `<Stars>`, `<Float>`, `<Grid>`. Postprocessing: `<Bloom>` + `<ChromaticAberration>`. Must lazy-load (React.lazy + Suspense) to protect initial bundle. |
| **Real-time WebSocket activity feed with animation** | Pipeline events stream in as animated list items: "Tweet collected", "Lead judged: RELEVANT", "Draft generated." The dashboard breathes. Current WebSocket infra exists but isn't connected to UI. | MEDIUM | Connect existing `useWebSocket` hook to a new `ActivityFeed` component. Magic UI `AnimatedList` for staggered entry animations. Motion `AnimatePresence` for enter/exit. Cap visible items at 20, virtualize if needed. |
| **HUD-style clipped card borders** (augmented-ui) | Angled corners, notched edges, and asymmetric clip-paths on panels. This is the visual language of every sci-fi movie HUD. Pure CSS, but dramatically changes silhouette. | MEDIUM | augmented-ui v2 `data-augmented-ui` attribute system. 8 mixin regions (tl, t, tr, r, br, b, bl, l). Apply to key panels: sidebar, metric cards, pipeline viewer. Needs careful integration with existing Tailwind classes. |
| **Ambient floating particle background** (tsParticles) | Slowly drifting luminous particles across the void background. Creates the "command center in space" atmosphere. Responds subtly to mouse movement. | MEDIUM | tsParticles React component with `loadSlim` bundle. Low particle count (30-50), slow speed, neon colors, connection lines disabled. Fixed position behind all content. Must not capture pointer events. |
| **Post-processing effects** (bloom, chromatic aberration) | Bloom makes neon elements physically glow beyond their bounds. Chromatic aberration adds the "through a lens" sci-fi feel. Makes R3F scenes look cinematic. | MEDIUM | @react-three/postprocessing `<EffectComposer>` with `<Bloom luminanceThreshold={0.6} mipmapBlur />` and subtle `<ChromaticAberration offset={[0.001, 0.001]} />`. Selective bloom by default (only emissive materials glow). GPU-dependent, needs quality toggle. |
| **Glitch effects on state changes** (errors, alerts, transitions) | Brief glitch distortion when errors occur or status changes. Communicates "system disruption" in-universe. Cyberpunk 2077's UI used this to signal damage/malfunction. | LOW | CYBERCORE CSS `data-cyber="glitch"` attribute. CSS-only `clip-path` animation. Apply to error toasts, rejected drafts, pipeline failures. Brief duration (200-400ms) so it's noticeable but not annoying. |
| **Staggered mount animations** (cards, table rows, list items) | Dashboard elements assemble themselves on page load like a HUD booting up. Each card slides/fades in with slight delay. Creates "system initializing" feel. | MEDIUM | Motion `staggerChildren` on parent containers. `initial={{ opacity: 0, y: 20 }}` to `animate={{ opacity: 1, y: 0 }}` with `transition={{ staggerChildren: 0.05 }}`. Apply to metric card grid, table rows, sidebar nav items. |
| **Animated data connections** (beams between related elements) | Visual lines connecting pipeline stages, or metric cards to their data sources. Magic UI `AnimatedBeam` traces SVG paths between DOM elements. | MEDIUM | Magic UI `AnimatedBeam` component. Needs ref-based positioning between source and target elements. Best applied between pipeline stages or on the Dashboard overview to connect metrics to the funnel. |
| **Sound effects on interactions** (optional, user-toggled) | Subtle sci-fi UI sounds on clicks, hovers, notifications. ARWES framework includes this as a core design primitive. Dramatically increases immersion. | MEDIUM | Howler.js (2KB gzip) for playback. Small sound sprite (< 50KB total). Sci-fi click, hover, notification, success, error sounds. Must be opt-in with clear toggle in Settings page. Muted by default. |
| **Responsive 2D fallback for mobile/low-end** | Full 3D experience on desktop, graceful degradation to 2D CSS-only effects on mobile/low-power. Maintains cyberpunk feel without R3F overhead. | MEDIUM | `matchMedia('(prefers-reduced-motion)')` + device capability detection. Skip R3F canvas, tsParticles, and heavy animations. Keep glassmorphism, neon colors, scanlines. CSS container queries for layout adaptation. |
| **Typing / terminal text reveal** | Key text elements (page titles, status messages) reveal character-by-character like a terminal printout. | LOW | CSS `steps()` animation or Magic UI `TypingAnimation`. Apply to page headers on mount. Brief (500-800ms). Don't apply to data values (readability). |
| **GSAP-driven complex timelines** (intro sequence, pipeline animations) | Multi-step choreographed animations that CSS alone can't achieve: elements moving along paths, synchronized transforms, scroll-triggered sequences. | HIGH | GSAP ScrollTrigger for scroll-based reveals. GSAP timeline for pipeline animation sequencing. Heavy library (45KB gzip), must justify each use. Best reserved for pipeline view and dashboard hero, not every page. |

### Anti-Features (Deliberately NOT Building)

Features that seem cool but actively harm the product. These are traps.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Aggressive full-screen glitch effects** | Constant glitch distortion causes eye strain, triggers photosensitivity issues, and makes data unreadable. Cyberpunk 2077 was criticized for overusing this. | Use glitch sparingly (error states only, 200-400ms duration). Never on data-bearing elements. Never continuous. |
| **3D charts (perspective bar/pie charts)** | 3D perspective on data charts distorts perception and makes values harder to compare. Every data viz expert warns against this. The dashboard UX research is unanimous: "Avoid 3D charts -- they distort perception." | Keep Recharts in 2D. Apply cyberpunk styling (neon gradients, glow) to flat charts. The aesthetic comes from color and glow, not from adding a z-axis to bar charts. |
| **Constant / looping heavy animations** | Continuous motion creates visual noise that competes with data. Users habituate within 30 seconds, then it's just a distraction eating GPU cycles. | Animate on state change, mount, and hover. Rest state should be mostly still with very subtle ambient movement (particles, scanlines). Respect `prefers-reduced-motion`. |
| **Auto-playing sound effects** | Unexpected sound in a web app is universally hated. Violates web accessibility guidelines. Users will close the tab. | Sound must be explicitly opt-in. Muted by default. Toggle in Settings page with clear label. Store preference in localStorage. |
| **Dense holographic overlays on data tables** | Layering holographic effects, scanlines, AND glass blur on data tables murders readability. Tables need to be scannable. | Apply cyberpunk styling to table container (borders, header). Keep cell content clean with high-contrast text. Glow effects on hover rows, not on resting content. |
| **Light mode / theme switcher** | Cyberpunk is defined by darkness. A light mode undermines the entire aesthetic and doubles the CSS work. No cyberpunk reference material uses light themes. | Single dark theme. Offer intensity controls (subtle vs. full effects) instead of a mode switch. |
| **Parallax scrolling on dashboard pages** | Dashboard content is functional, not editorial. Parallax creates motion sickness, breaks scroll position, and makes data tables unusable. | Use staggered mount animations instead. Scroll should be normal and predictable. Data-heavy pages must scroll naturally. |
| **Custom cursor replacement** | Custom cursors break accessibility, feel laggy, and confuse muscle memory. The novelty wears off in 5 seconds. | Use CSS `cursor: pointer` states normally. Add neon hover glow to interactive elements instead. |
| **Video backgrounds** | Autoplaying video backgrounds are massive performance hits, drain battery, and compete with actual content for attention. | Use R3F particle scene (GPU-efficient, interactive) or CSS gradient animation for ambient background. Much lighter, more controllable. |
| **Overloaded sidebar with animated icons** | Animating every sidebar icon creates visual chaos on the navigation that users interact with most frequently. | Static icons with neon color on active state. Animate only on hover (brief glow pulse). Keep navigation scannable and predictable. |

## Feature Dependencies

```
[Dark Void Background + Neon Color System]
    ├──requires──> (nothing, pure CSS foundation)
    └──enables──> [Everything else]

[Glassmorphism Panels]
    └──requires──> [Dark Void Background]

[Neon-Styled Recharts]
    └──requires──> [Neon Color System]

[Scanline/Noise Overlay]
    └──requires──> [Dark Void Background]

[Border Beam / Shine Effects]
    └──requires──> [Glassmorphism Panels] (needs transparent containers to look right)

[HUD Clipped Borders (augmented-ui)]
    └──requires──> [Glassmorphism Panels]
    └──conflicts-with──> [Border Beam on same element] (clip-path breaks border-radius)

[Animated Page Transitions]
    └──requires──> [Motion library installed]
    └──enables──> [Staggered Mount Animations]

[Staggered Mount Animations]
    └──requires──> [Motion library installed]

[3D Hero Background]
    └──requires──> [React Three Fiber + drei + postprocessing installed]
    └──enables──> [Post-Processing Effects]

[Post-Processing Effects (Bloom)]
    └──requires──> [3D Hero Background] (EffectComposer lives inside R3F Canvas)

[Ambient Particles (tsParticles)]
    └──independent──> (works without R3F, CSS-level layer)
    └──conflicts-with──> [3D Hero Background] (visual overlap — pick one per page)

[3D Pipeline Node Graph]
    └──requires──> [Neon Color System]
    └──requires──> [@xyflow/react + elkjs] OR [React Three Fiber]
    └──enhances──> [Real-time WebSocket Activity Feed]

[Real-time WebSocket Activity Feed]
    └──requires──> [Existing useWebSocket hook + Motion library]
    └──enhances──> [3D Pipeline Node Graph] (events trigger particle flow)

[Sound Effects]
    └──requires──> [Howler.js]
    └──requires──> [Settings page toggle control]
    └──independent of──> (all visual features)

[Responsive 2D Fallback]
    └──requires──> [All features built first, then add degradation paths]

[GSAP Timelines]
    └──conflicts-with──> [Motion for same elements] (don't mix animation libs on same DOM nodes)
    └──best-for──> [Pipeline View, Dashboard hero sequence]
```

### Dependency Notes

- **Color system + dark background are the foundation.** Every other feature depends on these CSS variables existing. Build first, costs almost nothing.
- **Glassmorphism panels are the second foundation.** Cards, modals, sidebar, tooltips all need the frosted glass treatment before adding border effects.
- **augmented-ui clip-paths conflict with border-radius.** On elements using HUD clipped borders, you cannot also use `BorderBeam` (which needs rounded corners for the traveling light). Choose one treatment per element.
- **tsParticles and R3F hero scene create visual overlap.** On the Dashboard page, use R3F hero background. On other pages where R3F isn't loaded, use tsParticles as a lighter alternative.
- **GSAP and Motion should not target the same DOM nodes.** Use Motion for component-level animations (mount, hover, layout). Use GSAP only for complex multi-element timeline sequences where Motion's API is insufficient.
- **WebSocket feed enhances pipeline graph.** When both exist, WS events can trigger particle emissions in the pipeline visualization. Build them independently but design the interface for composition.
- **Responsive fallback must come last.** You need the full-fat version working before you can define what degrades and how.

## MVP Definition

### Launch With (Phase 1: CSS Foundation)

Minimum viable cyberpunk -- the lowest-cost changes that create the most dramatic visual shift.

- [ ] **Dark void background + warm neon color system** -- CSS variables only, immediate transformation
- [ ] **Glassmorphism panels** -- replace all `bg-gray-800/50 border-gray-700` with frosted glass
- [ ] **Neon glow on interactive elements** -- hover/focus states emit light via `box-shadow`
- [ ] **Monospace typography for data values** -- `font-mono` class on numbers
- [ ] **Scanline overlay** -- single `::after` pseudo-element on layout wrapper
- [ ] **Neon-styled Recharts** -- gradient fills, neon axes, glassmorphism tooltips
- [ ] **Loading skeleton with neon pulse** -- replace `LoadingSpinner`
- [ ] **Animated number counters on metric cards** -- `NumberTicker` or Motion count-up

### Add After Foundation (Phase 2: Motion + Interaction)

Features that add life and movement once the visual base is solid.

- [ ] **Motion library integration** -- install + AnimatePresence on router
- [ ] **Animated page transitions** -- fade/slide between routes
- [ ] **Staggered mount animations** -- cards and rows assemble on load
- [ ] **Border beam effects on key cards** -- Magic UI `BorderBeam`
- [ ] **Glitch effects on error states** -- CYBERCORE CSS, brief duration
- [ ] **Typing text reveal on page headers** -- terminal-style character animation
- [ ] **Real-time WebSocket activity feed** -- connect existing hook, animated list

### Add After Motion (Phase 3: 3D + Pipeline)

The headline features that require heavier dependencies.

- [ ] **React Three Fiber 3D hero background** -- ambient scene behind Dashboard page
- [ ] **Post-processing bloom + chromatic aberration** -- makes neon elements physically glow
- [ ] **Pipeline node graph (2D first)** -- @xyflow/react DAG with animated edges
- [ ] **HUD clipped borders (augmented-ui)** -- angled corners on sidebar and key panels
- [ ] **Ambient particles (tsParticles)** -- floating particles on non-R3F pages

### Future Consideration (Phase 4+)

Features to defer until the core experience is polished.

- [ ] **3D pipeline particle flow** -- upgrade 2D xyflow pipeline to R3F instanced particles (Shopify BFCM technique). Defer because: requires custom shaders, GPU optimization, and the 2D version provides 80% of the value.
- [ ] **Sound effects** -- opt-in audio feedback. Defer because: requires sound asset creation/licensing, Settings toggle, and is polarizing with users.
- [ ] **GSAP complex timelines** -- choreographed intro sequences. Defer because: 45KB bundle weight, overlaps with Motion, only justified for hero moments.
- [ ] **Animated data connections (beams between elements)** -- Magic UI `AnimatedBeam` between metrics. Defer because: requires precise ref positioning and is fragile with responsive layouts.
- [ ] **Responsive 2D fallback** -- graceful degradation for mobile/low-end. Defer because: needs full experience working first, and primary use case is desktop.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Dark void + neon color system | HIGH | LOW | **P1** |
| Glassmorphism panels | HIGH | LOW | **P1** |
| Neon glow on interactives | HIGH | LOW | **P1** |
| Scanline overlay | MEDIUM | LOW | **P1** |
| Neon-styled Recharts | HIGH | MEDIUM | **P1** |
| Animated number counters | MEDIUM | LOW | **P1** |
| Monospace data typography | MEDIUM | LOW | **P1** |
| Loading skeleton neon pulse | MEDIUM | LOW | **P1** |
| Page transitions (Motion) | HIGH | MEDIUM | **P2** |
| Staggered mount animations | HIGH | MEDIUM | **P2** |
| Border beam on cards | MEDIUM | LOW | **P2** |
| Glitch on error states | MEDIUM | LOW | **P2** |
| Typing text reveal | LOW | LOW | **P2** |
| WebSocket activity feed | HIGH | MEDIUM | **P2** |
| R3F 3D hero background | HIGH | HIGH | **P2** |
| Post-processing (bloom) | MEDIUM | MEDIUM | **P2** |
| Pipeline node graph (2D) | HIGH | HIGH | **P2** |
| HUD clipped borders | MEDIUM | MEDIUM | **P2** |
| Ambient particles (tsParticles) | MEDIUM | MEDIUM | **P3** |
| 3D pipeline particle flow | HIGH | HIGH | **P3** |
| Sound effects | LOW | MEDIUM | **P3** |
| GSAP timelines | LOW | HIGH | **P3** |
| Animated beams | LOW | MEDIUM | **P3** |
| Responsive 2D fallback | MEDIUM | MEDIUM | **P3** |

**Priority key:**
- P1: CSS foundation -- must ship first, enables everything, low cost
- P2: Motion + 3D -- the differentiating features, ship after foundation
- P3: Polish + advanced -- nice to have, ship when core is solid

## Competitor Feature Analysis

| Feature | ARWES (sci-fi framework) | Cosmic UI (holographic) | Cyberpunk 2077 game UI | Shopify BFCM Globe | Our Approach |
|---------|--------------------------|-------------------------|------------------------|-------------------|--------------|
| Color system | Blue/cyan cold palette | Holographic rainbow | Yellow/red warm palette | Globe-specific (no dashboard) | Warm neons (pink/orange/gold) -- more distinctive than cold blues |
| Panel treatment | Animated borders with sound | Holographic glass | Minimal, functional | N/A | Glassmorphism + augmented-ui clip-paths + border beam |
| Data visualization | Not a focus | Not a focus | 2D minimalist charts | 3D globe with arcs | Neon 2D Recharts + 3D pipeline graph for flow data |
| Animation approach | react-transition-group + Howler | GSAP + custom | In-engine | R3F + custom shaders | Motion (primary) + GSAP (complex timelines) + R3F (3D scenes) |
| Pipeline visualization | None | None | None | Real-time arc flow (Bezier + instancing) | @xyflow/react DAG with animated edges, upgrade path to R3F particles |
| Sound | Core feature (always on) | None | Core feature (game) | None | Opt-in only, muted by default, Settings toggle |
| Performance strategy | Basic, not optimized | Unknown | Game engine (60fps native) | GPU instancing, WebGL optimization | Lazy-load R3F, selective bloom, `prefers-reduced-motion`, quality toggle |
| Maturity | Alpha (not production-ready) | Small community | Shipped game (not web) | Production (annual event) | Production-ready, progressive enhancement |

## Sources

- [Shopify BFCM 2023 Globe Engineering](https://shopify.engineering/how-we-built-shopifys-bfcm-2023-globe) -- HIGH confidence, first-party engineering writeup on R3F particle flow techniques
- [Shopify BFCM 3D Data Visualization](https://shopify.engineering/bfcm-3d-data-visualization) -- HIGH confidence, GPU instancing and shader techniques
- [Hersimu: Cyberpunk Aesthetics in Modern Web Design](https://www.hersimu.com/2025/05/27/cyberpunk-aesthetics/) -- MEDIUM confidence, provides conversion metrics (session duration +65%, bounce rate -29%)
- [excited.agency: Dashboard UX Design Best Practices](https://excited.agency/blog/dashboard-ux-design) -- HIGH confidence, comprehensive UX principles for dark dashboards
- [Medium/Domo UX: Functional Futuristic Interface Design](https://medium.com/domo-ux/designing-a-functional-futuristic-user-interface-c27d617ce8cc) -- MEDIUM confidence, principles for balancing aesthetics with usability
- [ARWES Sci-Fi Framework Documentation](https://arwes.dev/docs) -- HIGH confidence, official docs. Framework is alpha/not production-ready.
- [augmented-ui v2 Documentation](https://augmented-ui.com/docs/) -- HIGH confidence, official docs for HUD clip-path CSS system
- [Magic UI Components](https://magicui.design/docs/components) -- HIGH confidence, official component library docs
- [Aceternity UI Components](https://ui.aceternity.com/components) -- HIGH confidence, official component library (200+ components)
- [React Postprocessing: Bloom](https://react-postprocessing.docs.pmnd.rs/effects/bloom) -- HIGH confidence, official pmndrs docs
- [xyflow/React Flow](https://reactflow.dev/) -- HIGH confidence, official docs for node-based UI library
- [tsParticles GitHub](https://github.com/tsparticles/tsparticles) -- HIGH confidence, official repo
- [CYBERCORE CSS](https://dev.to/sebyx07/introducing-cybercore-css-a-cyberpunk-design-framework-for-futuristic-uis-2e6c) -- MEDIUM confidence, community framework
- [shadcn/ui Cyberpunk Theme](https://www.shadcn.io/theme/cyberpunk) -- MEDIUM confidence, community theme
- [Cyberpunk 2077 UX/UI Critique](https://interfaceingame.com/articles/cyberpunk-2077-ux-ui-critique/) -- MEDIUM confidence, useful anti-pattern analysis
- [Dribbble: Cyberpunk UI](https://dribbble.com/tags/cyberpunk-ui) -- LOW confidence (visual inspiration only)
- [Behance: Cyberpunk HUD UI](https://www.behance.net/gallery/114908415/Cyberpunk-HUD-UI-500) -- LOW confidence (visual inspiration only)
- [wawa-vfx Particle System for R3F](https://wawasensei.dev/blog/wawa-vfx-open-source-particle-system-for-react-three-fiber-projects) -- MEDIUM confidence, open-source alternative to custom particle systems

---
*Feature research for: Cyberpunk immersive dashboard UI*
*Researched: 2026-02-24*
