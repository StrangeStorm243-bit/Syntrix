# Terminal C — Ambient Effects & Motion → Hero 3D Scene

**Role:** Global effects layer (particles, transitions, stagger) then 3D hero background
**Phases:** 3 → 6 (hero 3D portion)
**Waits for:** Terminal A Phase 1 complete (Phase 3), Terminal D Phase 5 R3F patterns (Phase 6)

---

## Shared Conventions

See `v03terminalA.md` → "Shared Conventions" section for color palette, typography, file naming, import conventions, architectural rules, and coordination protocol. ALL terminals follow the same conventions.

---

## Phase 3: Ambient Effects & Motion Layer

**Requirements:** AE-01, AE-02, AE-03, AE-04, AE-05
**Blocks:** Terminal A Phase 4 (pages need transitions before upgrading)

### Step 1: Install Dependencies

```bash
cd dashboard
npm install @tsparticles/react @tsparticles/slim
```

Note: Motion should already be installed by Terminal B. If not, install it: `npm install motion`

### Step 2: Create Particle Background

**File: `dashboard/src/components/effects/ParticleBackground.tsx`**

```typescript
// Uses @tsparticles/react
// Config:
//   - Particles: small dots, color: var(--neon-primary) at 0.3 opacity
//   - Count: adaptive (100 desktop, 50 tablet, 30 mobile)
//   - Movement: slow drift upward (speed: 0.3)
//   - Links: enabled, distance 150, color var(--neon-primary) at 0.1 opacity
//   - Interactivity: hover repulse (subtle, distance 100)
//   - Background: transparent (overlays on --bg-void)
//
// Respects useReducedMotion — if reduced, renders static dots only (no movement)
// z-index: 0 (behind all content)
```

### Step 3: Create Page Transition

**File: `dashboard/src/components/effects/PageTransition.tsx`**

```typescript
import { motion, AnimatePresence } from 'motion/react';
import { useLocation } from 'react-router-dom';

// Wrap around <Outlet /> in CyberpunkLayout
// Uses AnimatePresence with mode="wait"
// Enter: opacity 0 → 1, y: 10 → 0 (300ms ease-out)
// Exit: opacity 1 → 0, y: 0 → -10 (200ms ease-in)
// Key: location.pathname
```

### Step 4: Create Stagger Mount Hook

**File: `dashboard/src/hooks/useStaggerMount.ts`**

```typescript
// Returns: { containerVariants, itemVariants, isReducedMotion }
// containerVariants: staggerChildren: 0.08 (or 0 if reduced motion)
// itemVariants: slideUp from animation-presets.ts (or instant if reduced motion)
// Used by pages to wrap grids/lists in <motion.div variants={containerVariants}>
```

### Step 5: Create Reduced Motion Hook

**File: `dashboard/src/hooks/useReducedMotion.ts`**

```typescript
// Listens to window.matchMedia('(prefers-reduced-motion: reduce)')
// Returns boolean
// Updates on media query change
// Used by ParticleBackground, PageTransition, all animation components
```

### Step 6: Create Scanlines Component

**File: `dashboard/src/components/effects/Scanlines.tsx`**

```typescript
// Renders a full-area overlay div with scanline CSS
// Props: opacity (0-1, default 0.03), className
// Purely decorative — pointer-events: none
// Can be mounted on any panel for CRT effect
```

### Step 7: Integrate into CyberpunkLayout

Update `CyberpunkLayout.tsx`:
1. Mount `<ParticleBackground />` as first child (z-0, absolute positioning)
2. Wrap `<Outlet />` with `<PageTransition>`
3. Import and pass `useReducedMotion()` context if needed

### Step 8: Verify & Commit

- Particles float in background across all pages
- Page transitions animate on route change
- Setting OS "reduce motion" disables all animations
- No performance regression on page navigation

```bash
git commit -m "feat(dashboard): Phase 3 — ambient effects, page transitions, motion accessibility"
```

**Signal to Terminal A: Phase 3 complete. Pages ready for upgrade.**

---

## Phase 6 (Partial): Hero 3D Scene

**Requirements:** HS-01, HS-02, HS-03
**Depends on:** Terminal D Phase 5 (R3F patterns established), Phase 2 (components exist)

### Prerequisites

Before starting, pull Terminal D's Phase 5 work. R3F, drei, and postprocessing packages will already be installed. The `scenes/` directory and lazy-load patterns will be established.

### Step 1: Create GPU Tier Hook

**File: `dashboard/src/hooks/useGPUTier.ts`**

```typescript
// Detects GPU capability:
//   HIGH: dedicated GPU (NVIDIA, AMD, Apple M-series) → full postprocessing + bloom
//   MEDIUM: integrated GPU (Intel UHD, Intel Iris) → no postprocessing, basic geometry
//   LOW: mobile/unknown/WebGL1 → no 3D at all, static CSS fallback
//
// Detection method:
//   const gl = canvas.getContext('webgl2');
//   const ext = gl.getExtension('WEBGL_debug_renderer_info');
//   const renderer = gl.getParameter(ext.UNMASKED_RENDERER_WEBGL);
//   Parse renderer string for GPU vendor keywords
//
// Returns: { tier: 'high' | 'medium' | 'low', renderer: string }
// Cache result in sessionStorage (GPU doesn't change mid-session)
```

### Step 2: Create Hero Scene

**File: `dashboard/src/scenes/HeroScene.tsx`**

```typescript
// R3F Canvas positioned absolutely behind Dashboard content
// Must be lazy-loaded via lazy3D() utility from Phase 1
//
// Scene contents:
//   - Ambient environment: dark fog, subtle directional light with pink tint
//   - Abstract geometry: slowly rotating wireframe icosahedron or torus knot
//     - Material: MeshStandardMaterial with emissive set to --neon-primary
//     - Wireframe: true
//     - Rotation: useFrame with ref (NOT setState)
//   - Floating particles: drei <Sparkles> with warm colors
//   - Camera: fixed perspective, subtle float using drei <Float>
//
// Post-processing (HIGH tier only):
//   - <EffectComposer>
//     - <Bloom luminanceThreshold={0.6} intensity={1.5} />
//     - <ChromaticAberration offset={[0.001, 0.001]} />
//   </EffectComposer>
//
// MEDIUM tier: Same geometry, no EffectComposer
// LOW tier: Don't render Canvas at all, use CSS gradient background fallback
//
// Performance:
//   - <Canvas frameloop="demand"> if scene is mostly static
//   - Or frameloop="always" with <AdaptiveDpr pixelated /> for auto quality scaling
```

### Step 3: Integrate into Dashboard Page

In Dashboard.tsx (already upgraded by Terminal A Phase 4):
- Import HeroScene via `lazy3D()`
- Render behind the metric card grid as absolute positioned background
- Pass GPU tier to conditionally render or skip

### Step 4: Create useDisposable Hook

**File: `dashboard/src/hooks/useDisposable.ts`**

```typescript
// Utility for Three.js resource cleanup
// On unmount: dispose geometry, material, texture for any Three.js object
// Usage: const ref = useDisposable<THREE.Mesh>()
// Prevents GPU memory leaks during navigation
//
// Implementation:
//   useEffect(() => {
//     return () => {
//       if (ref.current) {
//         ref.current.geometry?.dispose();
//         if (Array.isArray(ref.current.material)) {
//           ref.current.material.forEach(m => m.dispose());
//         } else {
//           ref.current.material?.dispose();
//         }
//       }
//     };
//   }, []);
```

### Step 5: Verify & Commit

- Hero scene renders behind Dashboard on HIGH/MEDIUM GPU tiers
- Bloom makes wireframe geometry glow pink
- LOW tier shows CSS gradient fallback
- Navigate away and back — no GPU memory growth
- No impact on page interactivity (3D is background only)

```bash
git commit -m "feat(dashboard): Phase 6 — hero 3D scene with GPU tier adaptation"
```

---

## Phase 7 Responsibilities (Terminal C)

Terminal C owns in Phase 7:
1. **prefers-reduced-motion comprehensive test** — verify every animation respects the setting
2. **GPU memory stability test** — navigate all 6 pages repeatedly for 30 minutes, monitor `renderer.info.memory`
3. **ParticleBackground performance** — verify particle count adapts on resize events
