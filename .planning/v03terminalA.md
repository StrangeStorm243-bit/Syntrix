# Terminal A — CSS Foundation → Dashboard & Analytics → Polish

**Role:** Foundation builder + page upgrader + final polish
**Phases:** 1 → 4 → 7

---

## Shared Conventions (ALL TERMINALS)

### Color Palette (CSS Custom Properties)
```css
--bg-void: #0a0608;
--bg-panel: #12090e;
--bg-glass: rgba(255, 40, 80, 0.05);
--neon-primary: #ff1493;      /* deep hot pink */
--neon-secondary: #ff6b35;    /* hot orange */
--neon-accent: #ffd700;       /* gold */
--neon-dim: #cc3366;          /* dimmed pink */
--text-primary: #ffe0ec;      /* warm white */
--text-secondary: #ffb3cc;    /* muted pink-white */
--text-data: #ff9955;         /* orange data values */
--border-glow: rgba(255, 20, 147, 0.4);
--glass-bg: rgba(18, 9, 14, 0.7);
--glass-border: rgba(255, 20, 147, 0.15);
```

### Typography
- **Headings:** System sans-serif (Inter or default)
- **Data values / metrics:** `JetBrains Mono` or `Orbitron` (monospace)
- **Body text:** System sans-serif

### File Naming
- Cyberpunk components: `dashboard/src/components/cyber/Neon*.tsx` or `Glass*.tsx`
- Effects: `dashboard/src/components/effects/*.tsx`
- 3D scenes: `dashboard/src/scenes/*.tsx` (lazy-loaded only)
- Pipeline: `dashboard/src/pipeline/*.tsx`
- Styles: `dashboard/src/styles/*.css`

### Import Conventions
- Motion: `import { motion, AnimatePresence } from 'motion/react'`
- GSAP: `import gsap from 'gsap'` + `import { useGSAP } from '@gsap/react'`
- R3F: ONLY in `scenes/` directory, always behind `React.lazy()`
- Three.js: NEVER import directly — use drei helpers or scenes/ isolation

### Architectural Rules
1. **Never `setState` inside `useFrame`** — use `useRef` and mutate `.current`
2. **Single `<Canvas>` at layout level** — use drei `<View>` for per-page 3D content
3. **All R3F imports lazy-loaded** — `React.lazy(() => import('./scenes/X'))`
4. **GSAP = DOM animations only** — never animate Three.js objects with GSAP directly
5. **Motion = React component enter/exit** — CSS transitions for hover/focus

### Coordination Protocol
- **Branch strategy:** Each terminal works on `feat/v04-tA`, `feat/v04-tB`, etc.
- **Merge order:** A → B → C → D (A merges to main first)
- **Shared files:** Only Terminal A touches `package.json` for Phase 1 deps. Others add their deps in their phases.
- **Signal "Phase 1 done":** Terminal A commits and pushes. Terminals B/C/D pull before starting.

---

## Phase 1: CSS Foundation & Design System

**Requirements:** DS-01, DS-02, DS-03, DS-04, DS-05, DS-06, DS-07
**Blocks:** Terminals B, C, D (all wait for this)

### Step 1: Install Foundation Dependencies

```bash
cd dashboard
npm install -D @tailwindcss/vite
# shadcn/ui init (follow Vite + React + Tailwind 4 guide)
npx shadcn@latest init
# Choose: TypeScript, Tailwind CSS, cyberpunk theme colors
```

Update `package.json` — add only Phase 1 deps:
- No 3D deps yet (those come in Phase 5)
- No Motion yet (Phase 2)

### Step 2: Create CSS Design Tokens

**File: `dashboard/src/styles/cyberpunk-vars.css`**
```css
@layer base {
  :root {
    /* Void backgrounds */
    --bg-void: #0a0608;
    --bg-panel: #12090e;
    --bg-elevated: #1a0f15;

    /* Neon accents */
    --neon-primary: #ff1493;
    --neon-secondary: #ff6b35;
    --neon-accent: #ffd700;
    --neon-dim: #cc3366;

    /* Glass */
    --glass-bg: rgba(18, 9, 14, 0.7);
    --glass-border: rgba(255, 20, 147, 0.15);
    --glass-blur: 16px;

    /* Text */
    --text-primary: #ffe0ec;
    --text-secondary: #ffb3cc;
    --text-muted: #996680;
    --text-data: #ff9955;

    /* Glow */
    --glow-sm: 0 0 5px var(--neon-primary), 0 0 10px rgba(255, 20, 147, 0.3);
    --glow-md: 0 0 10px var(--neon-primary), 0 0 30px rgba(255, 20, 147, 0.3);
    --glow-lg: 0 0 15px var(--neon-primary), 0 0 45px rgba(255, 20, 147, 0.3);
    --glow-orange: 0 0 10px var(--neon-secondary), 0 0 30px rgba(255, 107, 53, 0.3);
    --glow-gold: 0 0 10px var(--neon-accent), 0 0 30px rgba(255, 215, 0, 0.3);

    /* Fonts */
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  }
}
```

**File: `dashboard/src/styles/glassmorphism.css`**
```css
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
}
.glass-hover:hover {
  border-color: rgba(255, 20, 147, 0.3);
  box-shadow: var(--glow-sm);
}
```

**File: `dashboard/src/styles/scanlines.css`**
```css
.scanlines::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(255, 20, 147, 0.03) 2px,
    rgba(255, 20, 147, 0.03) 4px
  );
  z-index: 50;
}
```

### Step 3: Import Styles in `index.css`
```css
@import "tailwindcss";
@import "./styles/cyberpunk-vars.css";
@import "./styles/glassmorphism.css";
@import "./styles/scanlines.css";
```

### Step 4: Create CyberpunkLayout

**File: `dashboard/src/layouts/CyberpunkLayout.tsx`**

Replace `DashboardLayout`. Must render identically at first (same sidebar, same outlet) but scoped inside the new cyberpunk CSS vars. Background uses `--bg-void`. Apply `scanlines` class to main content area.

Key points:
- Keep existing `<Sidebar>` component (will be upgraded by Terminal B in Phase 2)
- Wrap `<Outlet />` in a div with `bg-[var(--bg-void)] text-[var(--text-primary)]`
- Add scanline overlay div
- Prepare a `<div id="canvas-root">` for future single persistent R3F Canvas (Phase 5/6)
- Keep existing React Query provider, router structure untouched

### Step 5: Create Lazy-Load Utility

**File: `dashboard/src/lib/lazy-3d.ts`**
```typescript
import { lazy, Suspense, type ComponentType } from 'react';

export function lazy3D<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
) {
  const LazyComponent = lazy(importFn);
  return function Lazy3DWrapper(props: React.ComponentProps<T>) {
    return (
      <Suspense fallback={<div className="animate-pulse bg-[var(--bg-panel)] rounded-lg h-64" />}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}
```

### Step 6: Update App.tsx Router

Replace `DashboardLayout` with `CyberpunkLayout` import. Everything else stays the same.

### Step 7: Verify No Regression

- All 6 pages render correctly through CyberpunkLayout
- Colors now use cyberpunk palette (dark void bg, warm text)
- Existing functionality unchanged
- Run existing tests: `npm test`

### Step 8: Commit & Signal

```bash
git add -A && git commit -m "feat(dashboard): Phase 1 — CSS foundation and cyberpunk design system"
git push origin feat/v04-tA
```

**Signal to other terminals: Phase 1 complete. Merge to main or coordinate.**

---

## Phase 4: Dashboard & Analytics Page Upgrades

**Requirements:** DP-01, DP-02, DP-03, AP-01, AP-02, AP-03
**Depends on:** Phase 1 (this terminal), Phase 2 (Terminal B — components), Phase 3 (Terminal C — transitions)
**Wait for:** Terminal B Phase 2 + Terminal C Phase 3 to merge before starting

### Step 1: Create Chart Theme

**File: `dashboard/src/lib/chart-theme.ts`**
```typescript
export const neonChartColors = {
  primary: '#ff1493',
  secondary: '#ff6b35',
  accent: '#ffd700',
  grid: 'rgba(255, 20, 147, 0.08)',
  axis: 'rgba(255, 224, 236, 0.3)',
  tooltip: {
    bg: 'rgba(18, 9, 14, 0.9)',
    border: 'rgba(255, 20, 147, 0.3)',
    text: '#ffe0ec',
  },
  gradients: {
    pinkToTransparent: ['#ff1493', 'rgba(255, 20, 147, 0)'],
    orangeToTransparent: ['#ff6b35', 'rgba(255, 107, 53, 0)'],
  },
};
```

### Step 2: Create CyberBarChart Wrapper

**File: `dashboard/src/components/cyber/CyberBarChart.tsx`**

Wraps Recharts `<BarChart>` with:
- Neon gradient `<defs>` for bar fills (pink→orange)
- Glassmorphism tooltip (`glass` class)
- Grid lines using `neonChartColors.grid`
- Axis labels in `--text-muted` color
- Animated bars on mount

### Step 3: Create CyberFunnelChart Wrapper

**File: `dashboard/src/components/cyber/CyberFunnelChart.tsx`**

Same pattern as CyberBarChart but for the funnel visualization.

### Step 4: Upgrade Dashboard.tsx

Replace existing metric cards with `NeonMetricCard` (from Terminal B Phase 2).
Replace existing Recharts with `CyberBarChart` / `CyberFunnelChart`.
Add Motion stagger animations for card grid mount (using presets from Phase 2).

### Step 5: Upgrade Analytics.tsx

Replace score distribution chart with `CyberBarChart`.
Replace funnel with `CyberFunnelChart`.
Replace query table with `NeonTable` (from Terminal B Phase 2).

### Step 6: Commit

```bash
git commit -m "feat(dashboard): Phase 4 — cyberpunk Dashboard and Analytics pages"
```

---

## Phase 7: Performance & Polish (ALL TERMINALS COLLABORATE)

**Requirements:** PP-01, PP-02, PP-03, PP-04, PP-05, PP-06, PP-07
**Depends on:** All phases 1-6 complete
**Terminal A owns:** Bundle verification, Vite config, WCAG audit

### Terminal A Responsibilities in Phase 7:

1. **Update `vite.config.ts`** with `manualChunks`:
   ```typescript
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           'vendor-3d': ['three', '@react-three/fiber', '@react-three/drei', '@react-three/postprocessing'],
           'vendor-flow': ['@xyflow/react', 'elkjs'],
           'vendor-motion': ['motion', 'gsap'],
         }
       }
     }
   }
   ```

2. **Verify initial bundle < 200KB** — run `npx vite-bundle-visualizer`

3. **WCAG AA contrast audit** — verify every text color against its background:
   - `--text-primary` (#ffe0ec) on `--bg-void` (#0a0608) → must be ≥ 4.5:1
   - `--text-data` (#ff9955) on `--bg-panel` (#12090e) → must be ≥ 4.5:1
   - `--neon-primary` (#ff1493) on `--bg-void` → check for decorative vs. informational use

4. **Run all existing tests** — verify the 4 test files still pass

5. **Final commit** after all terminals merge
