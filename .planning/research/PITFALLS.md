# Pitfalls Research

**Domain:** Cyberpunk immersive 3D dashboard (React Three Fiber + @xyflow/react + Motion + tsParticles on React 19 + Vite 7)
**Researched:** 2026-02-24
**Confidence:** HIGH (verified against official R3F docs, React Flow docs, and community post-mortems)

## Critical Pitfalls

### Pitfall 1: React State Driving the Animation Loop

**What goes wrong:**
Developers use `useState` or Redux state updates inside `useFrame` to animate 3D objects. This pumps 60 component re-renders per second through React's reconciler -- diffing, running all hooks, re-rendering the component and its entire subtree 60 times per second. The result is catastrophic frame drops, janky animations, and a UI that feels broken on anything less than a high-end desktop.

**Why it happens:**
React Three Fiber looks like React (JSX components, hooks), so developers reach for familiar React patterns. The mental model of "change state, React updates the DOM" does not translate to real-time animation. R3F's `useFrame` runs outside React's render cycle, but calling `setState` inside it forces React back into the loop.

**How to avoid:**
- Use `useRef` for all values that change at animation speed. Mutate `ref.current` properties directly inside `useFrame`.
- Use Zustand with transient subscriptions (`useStore.getState()` inside `useFrame`) for shared animation state -- this reads state without triggering React re-renders.
- Reserve `useState` for discrete, infrequent changes: toggle visibility, change color on click, switch scene modes.
- Lint rule: flag any `set*` call inside `useFrame` callbacks during code review.

**Warning signs:**
- React DevTools Profiler shows components rendering 60 times per second
- GPU is idle but CPU is pegged (React reconciliation is the bottleneck, not rendering)
- Animations stutter in exact sync with React component re-renders
- `useFrame` callbacks contain any `set*` calls from `useState`

**Phase to address:**
Phase 1 (Foundation/3D Infrastructure) -- establish the mutation-via-ref pattern in the very first `useFrame` usage. Create a project-level `useAnimatedValue` utility hook that enforces the ref-based pattern. All subsequent phases inherit this convention.

---

### Pitfall 2: WebGL Context Exhaustion from Multiple Canvas Instances

**What goes wrong:**
Browsers limit active WebGL contexts to 8-16 (browser-dependent). Each R3F `<Canvas>` creates a WebGL context. If the dashboard mounts separate canvases per page (hero background on Dashboard, pipeline graph on another page, particle effects on a third), navigating between pages accumulates contexts. Once the limit is hit, the oldest context is silently killed -- the 3D scene goes black with no error in the console. On Safari, the limit is as low as 8.

**Why it happens:**
React's component model encourages per-page encapsulation. Developers create a `<Canvas>` in each page component, and React Router unmounts/remounts them on navigation. R3F does call `forceContextLoss()` on unmount, but browser context recovery is not instant, and rapid navigation can exceed the limit before cleanup completes.

**How to avoid:**
- Use a single, persistent `<Canvas>` at the layout level (in `DashboardLayout.tsx`), rendering it once and never unmounting it.
- Route 3D content inside the canvas using a custom scene switcher or drei's `<View>` component, not React Router DOM routes.
- For the pipeline node graph (@xyflow/react), use SVG/HTML rendering (its default), NOT a second WebGL canvas. Keep React Flow and R3F on separate rendering layers (SVG overlay on WebGL).
- If a second canvas is absolutely needed (unlikely), limit total active contexts to 2 maximum and explicitly dispose the previous one before creating a new one.

**Warning signs:**
- Black/empty canvas areas after navigating between pages
- Console warning: "WARNING: Too many active WebGL contexts. Oldest context will be lost."
- Safari users report blank 3D scenes that work on Chrome
- Memory usage climbs steadily during navigation without dropping back

**Phase to address:**
Phase 1 (Foundation) -- the canvas architecture decision must be made before any 3D content is built. Retrofitting from per-page canvases to a single persistent canvas is a full rewrite of the 3D layer.

---

### Pitfall 3: GPU Memory Leaks from Undisposed Three.js Resources

**What goes wrong:**
Three.js geometries, materials, textures, and render targets allocate GPU memory that is NOT automatically garbage-collected by JavaScript. When components unmount (page navigation, conditional rendering, data updates that swap 3D objects), the GPU buffers persist in VRAM. Over a typical work session (hours of lead review), GPU memory grows unbounded. Eventually: visual glitches, browser tab crash, or system-wide GPU memory exhaustion.

**Why it happens:**
React's mental model is "unmount = cleanup." Developers expect that removing a `<mesh>` from the JSX tree frees its resources. R3F does remove the Three.js object from the scene graph, but it does NOT call `.dispose()` on geometries, materials, or textures -- that responsibility falls on the developer. This is invisible during development (short sessions, page refreshes) and only manifests in production usage patterns.

**How to avoid:**
- Create a `useDisposable` hook that tracks all Three.js resources created by a component and calls `.dispose()` on unmount.
- For GLTF models: traverse the scene graph on unmount and dispose every mesh's geometry, material, and textures (including maps like normalMap, roughnessMap, etc.).
- Use R3F's `useLoader` for all asset loading -- it caches globally and reduces duplicate allocation.
- For dynamically created geometries (particle systems, custom shapes): store references and dispose in cleanup functions.
- Monitor GPU memory in Chrome DevTools > Task Manager (`GPU Memory` column) during development. If it only goes up, you have a leak.

**Warning signs:**
- Chrome Task Manager shows `GPU Memory` growing with each page navigation
- `renderer.info.memory` (accessible via R3F's `useThree`) shows `geometries` and `textures` counts increasing over time
- Visual glitches or texture corruption after extended use
- Browser tab marked as "using significant memory" by OS

**Phase to address:**
Phase 1 (Foundation) -- establish disposal patterns alongside the first geometry/material creation. Create shared utilities (`disposeScene`, `useDisposable`). Every subsequent phase must follow disposal conventions.

---

### Pitfall 4: Post-Processing Bloom Destroying Mobile/Low-End Performance

**What goes wrong:**
Bloom post-processing (the signature neon glow effect of the cyberpunk aesthetic) renders the entire scene to an offscreen buffer, applies multi-pass Gaussian blur, then composites back. This effectively doubles or triples the GPU fragment shader workload. On integrated GPUs (Intel UHD, Apple M-series at low power), laptops in power-saver mode, or older dedicated GPUs, this drops frame rates from 60fps to 15-25fps. The dashboard becomes unusable for the actual task (reviewing leads).

**Why it happens:**
Bloom looks stunning in development on a developer's high-end machine. The performance cost is invisible until tested on real user hardware. Additionally, full-scene bloom is the easiest to implement but the most expensive -- every pixel gets the blur treatment regardless of whether it glows.

**How to avoid:**
- Use `SelectiveBloom` from `@react-three/postprocessing` to apply bloom only to objects in a specific layer (neon edges, glowing nodes), not the entire scene.
- Implement `drei`'s `PerformanceMonitor`: track average FPS, and when it drops below 45fps for 3 seconds, automatically disable post-processing effects. Store this preference so it persists.
- Set bloom resolution to half the canvas resolution (`resolutionScale: 0.5`) as default -- visually nearly identical, half the GPU cost.
- Provide a manual "Performance Mode" toggle in Settings that disables all post-processing.
- On mobile (detect via viewport width or `navigator.hardwareConcurrency < 4`): skip post-processing entirely, use CSS `box-shadow` with neon colors as a fallback glow.

**Warning signs:**
- FPS drops below 30 when bloom is enabled (check with `r3f-perf` or `drei`'s Stats)
- Laptop fans spin up noticeably on the dashboard page
- `renderer.info.render.calls` shows significantly more draw calls than scene objects
- Mobile users report "hot phone" or "battery drain" on the dashboard

**Phase to address:**
Phase 2 (3D Pipeline Scene) -- bloom is introduced here. PerformanceMonitor and SelectiveBloom must ship in the same phase, not as a "later optimization."

---

### Pitfall 5: Neon Aesthetic Destroying Text Readability and Accessibility

**What goes wrong:**
Hot pink (#ff1493) and gold (#ffd700) neon text on near-black (#0a0608) backgrounds can fail WCAG 2.1 AA contrast requirements (4.5:1 for normal text). Bloom glow effects on text make edges fuzzy and reduce legibility. Neon-on-neon combinations (pink text on orange-tinted panels) create eye strain during extended use. Data-heavy screens (Leads table, Analytics charts) become unusable as a daily work tool because users cannot read the actual data.

**Why it happens:**
Cyberpunk aesthetics prioritize visual impact over information density. Design inspiration comes from games (Cyberpunk 2077) and sci-fi films where text is read for seconds, not hours. A dashboard is read for hours daily. The aesthetic and the use case have fundamentally different readability requirements.

**How to avoid:**
- Separate "decorative" and "data" text categories. Decorative text (headings, labels) can use neon colors. Data text (table cells, metric values, timestamps) MUST use the warm white (`#ffe0ec`) or the orange data value color (`#ff9955`) with verified contrast ratios.
- Run every color combination through a WCAG contrast checker before shipping. Target 7:1 (AAA) for data text, 4.5:1 (AA) minimum for decorative text.
- Never apply bloom post-processing to text elements. Text lives in HTML/CSS overlay, not inside the WebGL canvas.
- Provide a "Data Focus" mode that strips decorative effects and maximizes data density (think: Bloomberg Terminal mode).
- Test with f.lux/Night Shift enabled -- warm screen filters shift neon pinks toward unreadable muddy tones.

**Warning signs:**
- Users squinting, increasing browser zoom, or complaining about "hard to read"
- WCAG audit tools flagging contrast failures on dashboard pages
- Data values in neon colors blending into glowing backgrounds
- Screenshots of the dashboard look great, but using it for 30 minutes causes eye fatigue

**Phase to address:**
Phase 1 (Design System/Theme) -- contrast ratios must be verified when the color system is established. Every subsequent phase inherits these verified color tokens. Revisit after Phase 2 (3D) to confirm bloom does not degrade text outside the canvas.

---

### Pitfall 6: React Flow Animated Edges CPU Bottleneck

**What goes wrong:**
React Flow's default `animated` edge prop uses CSS `stroke-dasharray` animation on SVG paths. With 8+ pipeline stages and edges between them (plus potential parallel paths), this creates multiple concurrent SVG animations that are not GPU-accelerated in most browsers. When combined with custom animated particles flowing along edges (the core pipeline visualization), CPU usage spikes. The pipeline graph drops to 20-30fps while the rest of the dashboard remains smooth, creating a jarring inconsistency.

**Why it happens:**
The `animated` prop on React Flow edges is a boolean -- flip it to `true` and it works. This simplicity hides the cost. SVG `stroke-dasharray` animations trigger continuous layout recalculations in the browser's compositor. Adding custom particle animations on top compounds the problem.

**How to avoid:**
- Do NOT use React Flow's built-in `animated` edge prop for the pipeline visualization.
- Use custom edge components with `<animateMotion>` SVG elements or the Web Animations API with `offsetPath` -- these are compositor-friendly and offloaded to GPU.
- For particle flow visualization: use a small number of actual animated elements (3-5 per edge) rather than rendering dozens. Use `requestAnimationFrame` directly, not React state updates.
- If edge count exceeds 20: batch animations using a single `requestAnimationFrame` loop that updates all edge particles, rather than per-edge animation loops.
- Memoize edge components with `React.memo` and extract animated sub-components to prevent parent re-renders from affecting animation smoothness.

**Warning signs:**
- Chrome Performance tab shows long "Recalculate Style" blocks during pipeline animation
- CPU usage climbs linearly with edge count
- Pipeline graph animation stutters while static pages remain smooth
- `stroke-dasharray` appears in Performance profiler flame graphs

**Phase to address:**
Phase 2 (Pipeline Node Graph) -- custom edge animation is a requirement from day one of the pipeline visualization, not a later optimization.

---

### Pitfall 7: Bundle Size Explosion from Eager Three.js Loading

**What goes wrong:**
Three.js core is ~600KB parsed (~155KB gzipped). Adding drei (~200KB), postprocessing (~150KB), and elkjs (~300KB) pushes the 3D dependency bundle to over 1MB parsed. If these are imported at the top level (static imports in route components), the initial page load downloads and parses all of this before showing any UI. The dashboard, which currently loads fast as a lightweight React SPA, suddenly has a 3-5 second blank screen on first visit.

**Why it happens:**
Vite's dev server uses native ESM and loads fast regardless. The problem only surfaces in production builds. Developers see instant loads in `vite dev` and assume production will be similar. Additionally, barrel exports (`import { Canvas, useFrame, useThree } from '@react-three/fiber'`) can defeat tree-shaking if any imported module has side effects.

**How to avoid:**
- Wrap ALL 3D components (Canvas, pipeline graph, particle backgrounds) in `React.lazy()` with `<Suspense>` boundaries.
- Create explicit code-split boundaries: `const PipelineScene = lazy(() => import('./scenes/PipelineScene'))`.
- Use Vite's `build.rollupOptions.output.manualChunks` to force Three.js, drei, and postprocessing into a separate `vendor-3d` chunk.
- Set loading priority: show the 2D dashboard immediately (metric cards, data tables), load 3D content after first paint.
- Measure: `vite build && npx vite-bundle-visualizer` to verify 3D deps are isolated from the main chunk.
- Target: initial chunk under 200KB parsed. 3D chunk loaded on demand.

**Warning signs:**
- `vite build` output shows a single chunk over 500KB
- Lighthouse "Time to Interactive" regresses by more than 1 second after adding 3D dependencies
- Users on slow connections see a blank page or loading spinner for 3+ seconds
- `import` statements for three/drei/postprocessing appear in non-3D page components

**Phase to address:**
Phase 1 (Foundation) -- lazy loading architecture must be established before any Three.js import enters the codebase. The first `import { Canvas } from '@react-three/fiber'` must be inside a `lazy()` boundary.

---

### Pitfall 8: GSAP and React Three Fiber Reconciler Conflict

**What goes wrong:**
GSAP timelines mutate DOM/object properties directly, bypassing React's reconciler. React Three Fiber also operates outside React DOM but uses its own custom React reconciler for the Three.js scene graph. When GSAP tweens a Three.js object's property (e.g., camera position), and React's reconciler simultaneously tries to set that same property from JSX props, the two systems fight. Results: jittery animations, properties snapping between GSAP's value and React's value, and non-interruptible animations that ignore user input.

**Why it happens:**
GSAP is listed as a key library for "complex sequenced timelines" in the project spec. Developers reach for it because it excels at choreographed multi-step animations. But GSAP's imperative mutation model fundamentally conflicts with R3F's declarative reconciler. This is not a bug -- it is an architectural mismatch.

**How to avoid:**
- Use GSAP exclusively for HTML/CSS DOM animations (page transitions, sidebar animations, HUD overlay effects) where it does not compete with R3F's reconciler.
- For 3D animations: use `maath`'s `easing.damp()` for smooth value chasing (frame-rate independent, interruptible) or `@react-spring/three` for spring-based 3D animations.
- If GSAP must animate Three.js properties: use a ref-based bridge pattern -- GSAP tweens a plain object (`{ x: 0, y: 0 }`), and `useFrame` reads from that object to apply values. GSAP never touches Three.js objects directly.
- Document the boundary explicitly: "GSAP = DOM layer, maath/springs = 3D layer."

**Warning signs:**
- 3D object properties "snap" or "jump" during animation
- Animations are not interruptible (user clicks during animation have no effect until it completes)
- GSAP `timeline.kill()` calls appearing as workarounds
- `ref.current.position` being set in both GSAP tweens and JSX props

**Phase to address:**
Phase 1 (Foundation) -- define the animation architecture boundary before any animation library is used. Document in the project's coding conventions which library handles which rendering layer.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Full-scene bloom instead of selective bloom | 5 minutes to implement vs 30 minutes | 2-3x GPU cost permanently, excludes low-end users | Never in production; OK for a proof-of-concept demo |
| `useState` for animation values | Familiar React pattern, works for simple cases | Re-render cascade, frame drops at scale | Never for values that change > 10x/second |
| Inline Three.js object creation in JSX | Less code, no separate geometry/material variables | New GPU allocations every re-render, memory growth | Never; always useMemo or define outside component |
| Skip `dispose()` on unmount | No visible effect during development | GPU memory grows 10-50MB per page navigation over sessions | Never; create disposal utility in Phase 1 |
| Static imports for Three.js | Simpler import statements | 600KB+ added to initial bundle, 3-5s load time regression | Never; lazy-load from day one |
| CSS `stroke-dasharray` for edge animation | Single boolean prop, instant result | CPU-bound animation, does not scale past 10 edges | Only acceptable for prototyping, replace before merge |
| Single pixel ratio (window.devicePixelRatio) | Sharp rendering on all devices | 4K displays render 4x pixels, destroying performance | Never; cap DPR at 2 and use PerformanceMonitor to lower |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| R3F + React Router | Mounting/unmounting `<Canvas>` on route change, causing context loss | Single persistent `<Canvas>` at layout level with content routing inside |
| @xyflow/react + R3F | Putting React Flow inside the WebGL canvas or using a second canvas for it | React Flow renders as HTML/SVG overlay; R3F renders background/ambient 3D. Separate DOM layers, shared data via Zustand |
| tsParticles + R3F | Running two independent animation loops (tsParticles requestAnimationFrame + R3F useFrame) | Use R3F's `useFrame` for particle updates if particles are inside the 3D scene, OR run tsParticles in a separate canvas layer with reduced particle count |
| WebSocket + 3D scene | Pushing every WebSocket message directly into React state, causing cascade re-renders of 3D components | Buffer WebSocket messages in a Zustand store or ref. Read from store inside `useFrame` at render time. Throttle UI updates to max 2-5 per second. |
| shadcn/ui + augmented-ui | Augmented-ui clip-paths conflict with shadcn's border-radius and overflow styling | Apply augmented-ui clip-paths to wrapper divs, not directly on shadcn components. Test each component combination explicitly. |
| Motion v12 + R3F | Using `<motion.div>` for elements that overlay the Canvas, causing layout shifts that desync HTML overlays from 3D content | Use `layoutId` animations only for non-overlay elements. For HUD overlays positioned over the canvas, use `transform` animations only (no layout shifts). |
| elkjs + React Flow | Calling elkjs layout synchronously on every node/edge change | elkjs runs asynchronously in a Web Worker. Debounce layout recalculation (300ms). Only re-layout when node count changes, not on every data update. |
| GSAP + R3F | GSAP tweening Three.js object properties directly | GSAP tweens a plain JS object; `useFrame` reads from that object. GSAP never references `ref.current` from R3F. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unthrottled WebSocket -> 3D updates | Every incoming tweet triggers a 3D particle spawn + React re-render; 10+ messages/second causes frame drops | Buffer messages, batch particle spawns to max 5/second, decouple 3D animation from data arrival | > 5 WebSocket messages per second |
| Per-frame Vector3 allocation | Smooth in short tests, GC pauses cause micro-stutters in long sessions | Reuse vectors with `.set()`, pre-allocate in module scope or `useMemo` | After 30+ minutes of continuous animation |
| Unscaled device pixel ratio | Silky on 1080p, slideshow on 4K/Retina displays | Cap DPR at 2.0 (`Math.min(window.devicePixelRatio, 2)`), PerformanceMonitor to reduce further | 4K monitors (3840x2160) or Retina MacBooks |
| Non-memoized React Flow custom nodes | Smooth with 6 pipeline nodes; re-renders cascade on any node data change | `React.memo()` on all custom node/edge components, extract animated sub-components | > 15 nodes or any node with animated children |
| tsParticles particle count not device-adaptive | Works on desktop, melts mobile CPUs | Detect device capability: desktop 150-200, tablet 80, mobile 30-50 particles. Disable line connections on mobile. | Mobile devices or laptops on battery |
| Bloom without resolution scaling | Full-res bloom on 1440p+ displays is 2-3x the GPU cost of 1080p | Set `resolutionScale: 0.5` on bloom effect, increase only if FPS budget allows | Displays > 1080p |
| React Flow accessing full nodes array in components | Imperceptible with 6 nodes; severe when nodes carry large data payloads | Use separate state for selection, avoid `nodes.filter()` in render, use `useStore` selectors | When node data objects contain full lead/draft data |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Loading GLTF/3D models from user-supplied URLs | Cross-site scripting via malicious GLTF files (embedded scripts in extensions), SSRF if server-side rendering | Only load 3D assets from bundled or whitelisted CDN paths. Never load from user input or API responses. |
| Exposing WebSocket messages in 3D visualization labels | Sensitive lead data (Twitter handles, profile info) visible in 3D scene text that might be screen-shared or screenshot | Use anonymized/truncated labels in 3D scene. Full data only in HTML overlay panels. |
| GPU fingerprinting via WebGL context | WebGL renderer info can uniquely identify users (GPU model, driver version) | Not a direct risk for a private dashboard, but note that `WEBGL_debug_renderer_info` extension exposes hardware details. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| 3D effects on data-heavy pages (Leads table, Queue) | Users cannot efficiently scan, sort, or act on data when 3D backgrounds compete for attention | 3D effects only on overview/dashboard page. Data pages use 2D cyberpunk styling (neon borders, glow shadows) without 3D. |
| No loading state for 3D scenes | 3-5 second blank canvas while Three.js initializes; users think page is broken | Show 2D fallback (CSS gradient + loading skeleton) immediately, crossfade to 3D once `<Canvas>` finishes first render. Use `<Suspense>` with styled fallback. |
| Animations on every interaction | Cool at first, annoying by day 3. Every button hover, every card click has a 300ms animation. Workflow speed is capped by animation duration. | Limit animations to: page transitions, first-load reveals, and explicit "show me more" interactions. Data interactions (approve, reject, filter) must be instant. |
| No way to disable effects | Users on low-end hardware or with vestibular disorders have no escape from motion | Respect `prefers-reduced-motion` OS setting (disable all animations, show static 2D fallback). Provide explicit "Reduce Effects" toggle in Settings. |
| Pipeline graph as sole navigation | Making the 3D pipeline graph the only way to navigate between pipeline stages | Pipeline graph is a visualization supplement, not a replacement for the existing sidebar navigation. Both paths must work. |
| Neon glow on interactive elements obscuring click targets | Bloom/glow makes button boundaries ambiguous -- users click the glow area expecting it to work | Use CSS `pointer-events` precisely, add subtle border on `:hover` to clarify clickable area. Test with bloom enabled. |

## "Looks Done But Isn't" Checklist

- [ ] **3D Scene:** Looks great on dev machine -- verify on integrated GPU laptop (Intel UHD 630), MacBook Air, and a 3-year-old Android phone in Chrome
- [ ] **Bloom effect:** Glows beautifully -- verify it does not bleed over HTML overlay text (metric values, table data)
- [ ] **Pipeline animation:** Particles flow smoothly -- verify FPS stays above 50 when a WebSocket sends 10 messages in 1 second
- [ ] **Page transitions:** Motion animations look smooth -- verify no layout shift when navigating from a 3D page to a 2D data page (canvas resize/hide)
- [ ] **Memory stability:** Works for 5 minutes -- verify GPU memory is stable after 30 minutes of navigation between all 6 pages
- [ ] **Bundle splitting:** Dev loads fast -- verify production build (`vite build`) keeps initial chunk under 200KB and 3D chunk loads on demand
- [ ] **Mobile fallback:** Desktop looks amazing -- verify mobile shows a graceful 2D fallback, not a crashed/blank canvas or 5fps slideshow
- [ ] **Accessibility:** Neon palette looks striking -- verify all data text passes WCAG AA (4.5:1) contrast. Test with Night Shift/f.lux warm filter enabled.
- [ ] **React Flow memoization:** Pipeline graph works -- verify custom node/edge components are wrapped in `React.memo` and don't re-render on unrelated state changes
- [ ] **`prefers-reduced-motion`:** Animations look cool -- verify OS reduced motion setting disables ALL animations (3D, particles, Motion transitions, edge flows) and shows usable static fallback
- [ ] **Dispose on unmount:** Scene unmounts cleanly -- verify `renderer.info.memory.geometries` and `.textures` counts return to baseline after navigating away from 3D pages
- [ ] **elkjs layout:** Auto-layout works -- verify it runs in a debounced async call, not synchronously on every render

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| State-driven animation loop | LOW | Replace `useState` with `useRef` in `useFrame` callbacks. Mechanical refactor, no architecture change. |
| Multiple canvas contexts | HIGH | Requires restructuring from per-page canvases to single persistent canvas. Affects routing, state management, and all 3D components. Plan 2-3 days. |
| GPU memory leaks | MEDIUM | Add `useDisposable` hook and traverse existing components to add disposal. Time-consuming but localized to each 3D component. |
| Bloom on low-end devices | LOW | Wrap existing bloom in `PerformanceMonitor` conditional. Add `SelectiveBloom` layer mask. Half-day refactor. |
| Unreadable neon text | LOW | Update CSS variables and color tokens. Mechanical change, but requires re-testing every page for contrast. |
| React Flow edge CPU bottleneck | MEDIUM | Replace `animated` boolean edges with custom `<animateMotion>` edge components. Requires rewriting edge rendering logic. |
| Bundle size bloat | MEDIUM-HIGH | Retrofitting lazy loading after static imports are spread across the codebase requires touching every file that imports Three.js. Much harder than doing it right from the start. |
| GSAP/R3F conflict | MEDIUM | Introduce ref-based bridge pattern between GSAP and useFrame. Requires rewriting affected animations but architecture stays intact. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| React state in animation loop | Phase 1: Foundation | Code review: zero `useState` calls inside `useFrame`. Profiler shows no 60fps re-renders. |
| WebGL context exhaustion | Phase 1: Foundation | Single `<Canvas>` in layout. Navigate all 6 pages rapidly 20 times -- no black screens. |
| GPU memory leaks | Phase 1: Foundation | `renderer.info.memory` geometries/textures stable after 50 page navigations. |
| Bloom performance | Phase 2: 3D Pipeline | PerformanceMonitor active. FPS > 45 on Intel UHD 630. Manual "Performance Mode" toggle exists. |
| Neon text readability | Phase 1: Design System | All data text colors pass WCAG AA (4.5:1). Automated contrast test in CI. |
| React Flow edge animation | Phase 2: Pipeline Graph | Custom edge components using `animateMotion` or Web Animations API. No `stroke-dasharray`. |
| Bundle size explosion | Phase 1: Foundation | `vite build` initial chunk < 200KB. Three.js in separate chunk loaded on demand. Bundle visualizer in CI. |
| GSAP/R3F conflict | Phase 1: Foundation | Architecture doc: "GSAP = DOM, maath = 3D." No GSAP imports inside R3F component tree. |
| WebSocket -> 3D update flood | Phase 2: 3D Pipeline | WebSocket messages buffered. Max 5 particle spawns/second. No re-renders from WebSocket events. |
| tsParticles mobile performance | Phase 3: Ambient Effects | Device-adaptive particle count. Mobile < 50 particles. Battery-saver disables particles. |
| No reduced-motion support | Phase 1: Foundation | `prefers-reduced-motion` check in place. All animation wrappers respect it. |
| Missing 3D loading states | Phase 2: 3D Pipeline | Every `<Suspense>` boundary has a styled 2D fallback. Sub-2-second perceived load time. |

## Sources

- [React Three Fiber Performance Pitfalls (official docs)](https://r3f.docs.pmnd.rs/advanced/pitfalls)
- [React Three Fiber Scaling Performance (official docs)](https://r3f.docs.pmnd.rs/advanced/scaling-performance)
- [React Flow Performance (official docs)](https://reactflow.dev/learn/advanced-use/performance)
- [Tuning Edge Animations in React Flow for Optimal Performance](https://liambx.com/blog/tuning-edge-animations-reactflow-optimal-performance)
- [React Flow Animated Edges Examples](https://reactflow.dev/examples/edges/animating-edges)
- [React Flow Large Graph Discussion (GitHub)](https://github.com/xyflow/xyflow/discussions/4975)
- [R3F + GSAP Discussion (GitHub)](https://github.com/pmndrs/react-three-fiber/discussions/565)
- [GSAP + R3F Performance Issues (GSAP Forum)](https://gsap.com/community/forums/topic/43299-performance-issues-on-desktop-and-mobile-devices-using-gsap-with-react-three-fiber/)
- [WebGL Context Lost in R3F (GitHub Discussion)](https://github.com/pmndrs/react-three-fiber/discussions/723)
- [Too Many WebGL Contexts on Safari (GitHub Discussion)](https://github.com/pmndrs/react-three-fiber/discussions/2457)
- [Three.js Memory Leak Disposal Patterns (Forum)](https://discourse.threejs.org/t/dispose-things-correctly-in-three-js/6534)
- [SelectiveBloom Documentation](https://react-postprocessing.docs.pmnd.rs/effects/selective-bloom)
- [Motion for React Accessibility](https://motion.dev/docs/react-accessibility)
- [Cyberpunk 2077 HUD UX Analysis (Medium)](https://medium.com/super-jump/a-ux-analysis-of-cyberpunk-2077s-hud-f74afe6b9961)
- [Building Efficient Three.js Scenes (Codrops, 2025)](https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/)
- [100 Three.js Tips That Actually Improve Performance (2026)](https://www.utsubo.com/blog/threejs-best-practices-100-tips)
- [Dashboard Design Disasters (Raw.Studio)](https://raw.studio/blog/dashboard-design-disasters-6-ux-mistakes-you-cant-afford-to-make/)
- [Motion Design Mistakes and Fixes (LogRocket)](https://blog.logrocket.com/ux-design/motion-design-mistakes-and-fixes/)
- [R3F Bundle Size Reduction Discussion (GitHub)](https://github.com/pmndrs/react-three-fiber/discussions/812)

---
*Pitfalls research for: Cyberpunk immersive 3D dashboard (React 19 + Vite 7 + R3F + @xyflow/react)*
*Researched: 2026-02-24*
