# Phase 1: CSS Foundation & Design System - Research

**Researched:** 2026-02-24
**Domain:** CSS design system, shadcn/ui theming, Tailwind CSS v4 custom properties, cyberpunk visual identity
**Confidence:** HIGH

## Summary

Phase 1 establishes the cyberpunk visual foundation for the Syntrix dashboard. The existing codebase is a React 19 + Vite 7 + Tailwind CSS 4 SPA with 6 pages rendered through a `DashboardLayout` wrapper. The current styling uses raw Tailwind utility classes with gray-scale colors (gray-700, gray-800, gray-900, gray-950). No component library is installed. The `cn` utility exists but uses only `clsx` -- it lacks `tailwind-merge` which shadcn/ui requires.

The core work involves: (1) defining a cyberpunk oklch color palette as CSS custom properties, (2) initializing shadcn/ui with Tailwind v4 theming, (3) creating glassmorphism/scanline/glow CSS utilities, (4) replacing `DashboardLayout` with a new `CyberpunkLayout`, and (5) laying architectural groundwork for future 3D lazy-loading. The approach is progressive enhancement -- existing pages must continue working throughout.

**Primary recommendation:** Initialize shadcn/ui via CLI (`npx shadcn@latest init`), then layer cyberpunk CSS custom properties on top of shadcn's theme variable structure using the `@theme inline` directive. Create effect CSS files (glassmorphism, scanlines, glow) as standalone imports. Replace DashboardLayout with CyberpunkLayout that applies the new visual identity while preserving the existing Sidebar + Outlet structure.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Cyberpunk warm palette: dark void bg (#0a0608), hot pink (#ff1493), orange (#ff6b35), gold (#ffd700)
- CSS custom properties using oklch color space for perceptual uniformity
- All colors exposed as `--cyber-*` CSS vars for downstream components
- Frosted glass utility classes: `backdrop-blur`, translucent backgrounds, subtle neon border glow
- Reusable as utility classes (not component-locked) so any element can be glass
- Box-shadow glow states on hover/focus for interactive elements (buttons, links, inputs)
- Glow color derived from the cyberpunk palette (pink/orange primary glows)
- Subtle CRT overlay texture applied across panels
- Repeating gradient scanline pattern, low opacity for readability
- Monospace HUD typography for data values (JetBrains Mono or Orbitron)
- Standard body font retained for readability of prose content
- Initialize shadcn/ui CLI with cyberpunk oklch theme variables
- `components.json` configured, theme tokens set
- CyberpunkLayout wrapper replaces existing DashboardLayout
- All 6 existing pages nest inside CyberpunkLayout
- No visual regression in functionality -- progressive enhancement
- `lazy-3d.ts` utility for lazy-loading future 3D imports (React.lazy + Suspense patterns)
- Single-canvas strategy documented (one persistent Canvas at layout level)
- `useRef` animation convention documented (never setState inside useFrame)
- R3F v9 for 3D, @xyflow for pipeline DAG, Motion v12 for 2D animations, GSAP for timelines (tech stack locked)
- shadcn/ui + Magic UI for component primitives

### Claude's Discretion
- Exact oklch values derived from the hex palette
- Scanline animation speed and density
- Glassmorphism blur radius and opacity values
- Specific shadcn/ui component variants to override
- CSS custom property naming convention details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DS-01 | Dashboard uses cyberpunk warm color palette (dark void bg #0a0608, hot pink #ff1493, orange #ff6b35, gold #ffd700) via CSS custom properties | oklch color conversion computed, `@theme inline` + `:root` CSS variable pattern documented, `--cyber-*` naming convention established |
| DS-02 | All panels use glassmorphism styling (backdrop-blur, translucent bg, subtle neon border glow) | Glassmorphism CSS pattern documented with `backdrop-filter: blur()` + rgba/oklch backgrounds + box-shadow, utility class approach established |
| DS-03 | Interactive elements have neon glow states on hover/focus via box-shadow | CSS `box-shadow` with oklch palette colors, `:hover`/`:focus-visible` selectors, Tailwind `@apply` pattern for utilities documented |
| DS-04 | Scanline/noise overlay applied as subtle CRT effect across panels | `repeating-linear-gradient` + `::after` pseudo-element + `pointer-events: none` pattern documented |
| DS-05 | Data values use monospace typography (JetBrains Mono or Orbitron) for HUD readability | JetBrains Mono available via Google Fonts, Fontsource, or self-hosted; Tailwind `@theme` font-family integration documented |
| DS-06 | shadcn/ui initialized with cyberpunk CSS variable theme (oklch color space) | Full manual installation procedure, dependencies list, `components.json`, CSS variable mapping, and `@theme inline` directive documented |
| DS-07 | CyberpunkLayout wrapper replaces existing DashboardLayout with no visual regression | Existing DashboardLayout structure analyzed (Sidebar + Outlet), progressive replacement strategy documented |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tailwindcss | ^4.2.1 | Utility-first CSS framework | Already installed; v4 uses `@theme` directive for custom properties natively |
| @tailwindcss/vite | ^4.2.1 | Vite plugin for Tailwind | Already installed; required for Tailwind v4 |
| shadcn (CLI) | @latest | Component scaffolding CLI | Official shadcn/ui installer; generates `components.json`, installs deps |
| class-variance-authority | latest | Component variant management | Required by shadcn/ui components for variant props |
| tailwind-merge | latest | Tailwind class deduplication | Required by shadcn/ui `cn()` utility; prevents conflicting Tailwind classes |
| clsx | ^2.1.1 | Conditional classname joining | Already installed; used by `cn()` utility |
| tw-animate-css | latest | Tailwind animation utilities | Required by shadcn/ui for enter/exit animations |
| lucide-react | ^0.575.0 | Icon library | Already installed; shadcn/ui default icon library |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fontsource-variable/jetbrains-mono | latest | Self-hosted JetBrains Mono variable font | For monospace HUD typography (DS-05); avoids Google Fonts CORS/latency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @fontsource-variable/jetbrains-mono | Google Fonts CDN import | CDN adds external dependency and FOIT; Fontsource bundles with app for zero latency |
| @fontsource-variable/jetbrains-mono | Orbitron font | Orbitron is display-only (no italic/weight range); JetBrains Mono is a proper variable monospace with full weight support (100-800) |
| Manual shadcn/ui setup | `npx shadcn@latest init` CLI | CLI handles deps + cn utility + CSS setup automatically; manual only needed if CLI fails |

**Installation:**
```bash
cd dashboard
npm install tailwind-merge class-variance-authority tw-animate-css @fontsource-variable/jetbrains-mono
npx shadcn@latest init
```

Note: `npx shadcn@latest init` will install `shadcn`, `class-variance-authority`, `clsx`, `tailwind-merge`, `tw-animate-css`, and `lucide-react` automatically. Since `clsx` and `lucide-react` are already installed, the CLI will skip them. Running the CLI is the recommended path -- only fall back to manual installation if the CLI errors.

## Architecture Patterns

### Recommended Project Structure
```
dashboard/src/
├── styles/
│   ├── cyberpunk-vars.css      # --cyber-* CSS custom properties (oklch palette)
│   ├── scanlines.css           # CRT overlay effect
│   └── glassmorphism.css       # Glass utility classes
├── layouts/
│   ├── DashboardLayout.tsx     # KEEP (unchanged, for rollback safety)
│   └── CyberpunkLayout.tsx     # NEW root layout (wraps Sidebar + Outlet + scanlines)
├── components/
│   └── ui/                     # shadcn/ui generated components (future phases)
├── lib/
│   ├── utils.ts                # MODIFY: upgrade cn() to use tailwind-merge
│   └── lazy-3d.ts              # NEW: React.lazy wrappers for 3D imports
└── index.css                   # MODIFY: add @import for cyberpunk styles + shadcn
```

### Pattern 1: CSS Custom Properties via `@theme inline` + `:root`
**What:** Define cyberpunk palette as CSS variables in `:root`, expose them to Tailwind via `@theme inline` directive.
**When to use:** For all theme colors that should be usable as both `var(--cyber-pink)` in CSS and `bg-cyber-pink` in Tailwind classes.
**Example:**
```css
/* Source: Tailwind CSS v4 docs (tailwindcss.com/docs/theme) + shadcn/ui manual install docs */

@import "tailwindcss";
@import "tw-animate-css";

/* Cyberpunk palette as :root vars */
:root {
  --cyber-void: oklch(0.130 0.010 345.1);
  --cyber-pink: oklch(0.655 0.261 356.9);
  --cyber-orange: oklch(0.705 0.193 39.2);
  --cyber-gold: oklch(0.887 0.182 95.3);
  --cyber-pink-dim: oklch(0.400 0.160 356.9);
  --cyber-orange-dim: oklch(0.450 0.120 39.2);
  --cyber-gold-dim: oklch(0.550 0.110 95.3);

  /* shadcn/ui semantic tokens mapped to cyberpunk palette */
  --background: oklch(0.130 0.010 345.1);
  --foreground: oklch(0.920 0.010 95.3);
  --primary: oklch(0.655 0.261 356.9);
  --primary-foreground: oklch(0.985 0 0);
  /* ... etc */
}

/* Expose to Tailwind v4 utility classes */
@theme inline {
  --color-cyber-void: var(--cyber-void);
  --color-cyber-pink: var(--cyber-pink);
  --color-cyber-orange: var(--cyber-orange);
  --color-cyber-gold: var(--cyber-gold);
  --color-cyber-pink-dim: var(--cyber-pink-dim);
  --color-cyber-orange-dim: var(--cyber-orange-dim);
  --color-cyber-gold-dim: var(--cyber-gold-dim);

  /* shadcn/ui required mappings */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  /* ... full list from shadcn/ui manual install */

  /* Font family */
  --font-mono: "JetBrains Mono Variable", ui-monospace, SFMono-Regular, monospace;
}
```

This enables both:
- `className="bg-cyber-pink text-cyber-gold"` (Tailwind utilities)
- `background: var(--cyber-pink)` (raw CSS)

### Pattern 2: Glassmorphism Utility Classes
**What:** Standalone CSS classes that apply frosted glass effect via `backdrop-filter`, translucent background, and optional neon border.
**When to use:** Apply to any card, panel, or container element to give it a glass appearance.
**Example:**
```css
/* Source: glassmorphism pattern (freefrontend.com, glass.ui, Josh W. Comeau) */

.glass {
  background: oklch(0.130 0.010 345.1 / 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid oklch(0.655 0.261 356.9 / 0.15);
}

.glass-strong {
  background: oklch(0.130 0.010 345.1 / 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid oklch(0.655 0.261 356.9 / 0.25);
  box-shadow: 0 0 15px oklch(0.655 0.261 356.9 / 0.1);
}

.glass-hover {
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.glass-hover:hover {
  border-color: oklch(0.655 0.261 356.9 / 0.4);
  box-shadow: 0 0 20px oklch(0.655 0.261 356.9 / 0.15);
}
```

### Pattern 3: Neon Glow States
**What:** Box-shadow based glow on hover/focus for interactive elements.
**When to use:** Buttons, links, inputs, any interactive element.
**Example:**
```css
/* Source: cyberpunk UI pattern, box-shadow technique */

.neon-glow {
  transition: box-shadow 0.2s ease;
}
.neon-glow:hover {
  box-shadow:
    0 0 5px oklch(0.655 0.261 356.9 / 0.5),
    0 0 20px oklch(0.655 0.261 356.9 / 0.3),
    0 0 40px oklch(0.655 0.261 356.9 / 0.1);
}
.neon-glow:focus-visible {
  outline: none;
  box-shadow:
    0 0 5px oklch(0.705 0.193 39.2 / 0.5),
    0 0 20px oklch(0.705 0.193 39.2 / 0.3);
}

.neon-glow-orange:hover {
  box-shadow:
    0 0 5px oklch(0.705 0.193 39.2 / 0.5),
    0 0 20px oklch(0.705 0.193 39.2 / 0.3),
    0 0 40px oklch(0.705 0.193 39.2 / 0.1);
}
```

### Pattern 4: Scanline CRT Overlay
**What:** A CSS pseudo-element overlay that creates a subtle CRT scanline texture.
**When to use:** Applied once at the layout level, covering the entire viewport.
**Example:**
```css
/* Source: aleclownes.com/2017/02/01/crt-display.html, dev.to/ekeijl/retro-crt-terminal-screen */

.scanlines::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    oklch(0 0 0 / 0.03) 2px,
    oklch(0 0 0 / 0.03) 4px
  );
  /* Optional slow scroll animation */
  animation: scanline-scroll 8s linear infinite;
}

@keyframes scanline-scroll {
  from { transform: translateY(0); }
  to { transform: translateY(4px); }
}
```

### Pattern 5: React.lazy Wrapper for 3D Imports
**What:** A typed utility function that wraps `React.lazy()` with proper Suspense boundary for heavy 3D modules.
**When to use:** All future R3F/Three.js component imports.
**Example:**
```typescript
// Source: React official docs (react.dev/reference/react/lazy)
import { lazy, Suspense, type ComponentType, type ReactNode } from 'react';

/**
 * Lazy-load a 3D component with a Suspense boundary.
 * Ensures Three.js/R3F code is code-split from the main bundle.
 */
export function lazy3D<T extends ComponentType<unknown>>(
  factory: () => Promise<{ default: T }>,
) {
  return lazy(factory);
}

/**
 * Suspense wrapper for 3D content with a standard fallback.
 */
export function Suspense3D({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return <Suspense fallback={fallback}>{children}</Suspense>;
}
```

### Anti-Patterns to Avoid
- **setState inside useFrame:** R3F renders at 60fps; calling setState causes React re-renders per frame, destroying performance. Always use `useRef` to mutate Three.js objects directly.
- **Multiple Canvas elements:** Each `<Canvas>` creates a separate WebGL context. Browsers limit WebGL contexts (typically 8-16). Use ONE Canvas at the layout level with scene management inside it.
- **Hardcoding oklch values in components:** Always reference `var(--cyber-*)` CSS variables or Tailwind `cyber-*` utilities. Never write raw oklch values in component JSX.
- **Importing Three.js at the top level:** Three.js is ~500KB+ gzipped. Always use `React.lazy()` or dynamic `import()` to code-split 3D modules.
- **Nesting backdrop-filter elements:** Stacking multiple `backdrop-filter: blur()` elements causes compounding GPU compositing. Use glass effect on container level, not nested children.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tailwind class conflict resolution | Custom class deduplication | `tailwind-merge` | Handles all Tailwind class conflicts (e.g., `bg-red-500 bg-blue-500` resolves correctly); constantly updated for new Tailwind versions |
| Component variant management | Custom prop-to-class mapping | `class-variance-authority` (CVA) | Type-safe variant definitions, compound variants, default variants; standard in shadcn/ui ecosystem |
| Font self-hosting | Manual @font-face declarations | `@fontsource-variable/jetbrains-mono` | Handles woff2 variable font bundling, font-display, weight ranges; single import line |
| CSS animation utilities | Custom keyframes for enter/exit | `tw-animate-css` | shadcn/ui depends on it; provides slide/fade/zoom animations as Tailwind utilities |
| Color space conversion | Manual oklch math | Online tools (oklch.com, oklch.fyi) | oklch has non-trivial perceptual uniformity math; use verified converters for one-time palette derivation |

**Key insight:** The shadcn/ui ecosystem has standardized on a specific dependency set (`tailwind-merge` + `clsx` + `class-variance-authority` + `tw-animate-css`). Fighting this by using alternatives will cause friction when adding shadcn/ui components in later phases.

## Common Pitfalls

### Pitfall 1: Existing `cn()` utility diverges from shadcn/ui expectation
**What goes wrong:** The current `cn()` in `lib/utils.ts` uses only `clsx` -- it does NOT use `tailwind-merge`. When shadcn/ui components are added, conflicting Tailwind classes will not be resolved correctly (e.g., passing `className="bg-red-500"` to a component with default `bg-blue-500` will apply BOTH, not override).
**Why it happens:** The dashboard was built before shadcn/ui was chosen.
**How to avoid:** Upgrade `cn()` to `twMerge(clsx(inputs))` during Phase 1 initialization. This is backward-compatible -- `tailwind-merge` wrapping `clsx` produces identical output when there are no conflicts.
**Warning signs:** Visual glitches where two background colors seem to fight, or hover states not overriding default styles.

### Pitfall 2: `@theme inline` vs `@theme` (without inline)
**What goes wrong:** Using `@theme` without `inline` causes Tailwind to generate utility classes that reference the variable NAME rather than its value. With `inline`, the generated CSS uses `var(--cyber-pink)` which correctly resolves at runtime.
**Why it happens:** Tailwind v4 has two `@theme` modes. The `inline` keyword tells Tailwind to emit `var()` references rather than inlining the resolved value.
**How to avoid:** Always use `@theme inline { ... }` when mapping `:root` CSS variables to Tailwind color utilities.
**Warning signs:** Colors not updating when CSS variables are changed; `oklch()` values appearing directly in compiled CSS instead of `var()` references.

### Pitfall 3: `backdrop-filter` not working without transparency
**What goes wrong:** `backdrop-filter: blur()` has no visible effect if the element's background is fully opaque.
**Why it happens:** The blur operates on content BEHIND the element. If `background: #000` (fully opaque), nothing behind is visible, so blur is invisible.
**How to avoid:** Always pair `backdrop-filter` with a translucent background: `background: oklch(0.130 0.010 345.1 / 0.6)` (note the `/0.6` alpha).
**Warning signs:** Glass elements looking like solid colored boxes with no frosted effect.

### Pitfall 4: Scanline overlay blocking interaction
**What goes wrong:** A fixed-position scanline overlay covers the entire viewport. Without `pointer-events: none`, it intercepts all clicks and hovers, making the app completely unresponsive.
**Why it happens:** Fixed/absolute positioned elements are above other content in stacking order by default.
**How to avoid:** Always set `pointer-events: none` on scanline overlays. Verify this with z-index management.
**Warning signs:** Buttons, links, inputs not responding to clicks; hover states not triggering.

### Pitfall 5: Missing `-webkit-backdrop-filter` vendor prefix
**What goes wrong:** `backdrop-filter` is not supported without the `-webkit-` prefix on Safari (iOS and macOS).
**Why it happens:** Safari still requires the vendor prefix as of 2025/2026 for some older versions.
**How to avoid:** Always include both: `backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);`
**Warning signs:** Glass effect works in Chrome/Firefox but shows as a solid rectangle on Safari.

### Pitfall 6: Path alias `@/` not configured for shadcn/ui
**What goes wrong:** shadcn/ui CLI expects `@/` path aliases (e.g., `import { cn } from "@/lib/utils"`). The current project does NOT have `@/` aliases configured in `tsconfig.json` or `vite.config.ts`.
**Why it happens:** The original Vite scaffold did not configure path aliases.
**How to avoid:** Add `baseUrl` and `paths` to `tsconfig.json` AND `resolve.alias` to `vite.config.ts` BEFORE running `npx shadcn@latest init`.
**Warning signs:** shadcn CLI init fails with path resolution errors; TypeScript errors on `@/` imports after adding components.

### Pitfall 7: Font loading FOIT (Flash of Invisible Text)
**What goes wrong:** Custom fonts cause text to be invisible while the font loads, then flash visible, creating a jarring user experience.
**Why it happens:** Default font-display behavior hides text until the custom font loads.
**How to avoid:** Use `font-display: swap` (Fontsource does this by default) so the system font shows immediately and swaps when custom font loads. For a cyberpunk app, the brief system font flash is acceptable.
**Warning signs:** Blank text areas on initial page load, especially on slower connections.

## Code Examples

### Complete `index.css` Structure (after Phase 1)
```css
/* Source: shadcn/ui manual install docs + Tailwind v4 docs */
@import "tailwindcss";
@import "tw-animate-css";

/* Cyberpunk custom styles */
@import "./styles/cyberpunk-vars.css";
@import "./styles/glassmorphism.css";
@import "./styles/scanlines.css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  /* Cyberpunk palette -> Tailwind utilities */
  --color-cyber-void: var(--cyber-void);
  --color-cyber-pink: var(--cyber-pink);
  --color-cyber-orange: var(--cyber-orange);
  --color-cyber-gold: var(--cyber-gold);
  --color-cyber-pink-dim: var(--cyber-pink-dim);
  --color-cyber-orange-dim: var(--cyber-orange-dim);
  --color-cyber-gold-dim: var(--cyber-gold-dim);
  --color-cyber-surface: var(--cyber-surface);
  --color-cyber-surface-bright: var(--cyber-surface-bright);
  --color-cyber-text: var(--cyber-text);
  --color-cyber-text-dim: var(--cyber-text-dim);

  /* shadcn/ui required semantic tokens */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);

  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);

  /* Typography */
  --font-mono: "JetBrains Mono Variable", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### oklch Color Palette Values (Computed)
```css
/* Source: computed from hex values via oklch conversion algorithm */
:root {
  /* Primary cyberpunk palette */
  --cyber-void: oklch(0.130 0.010 345.1);       /* #0a0608 - dark background */
  --cyber-pink: oklch(0.655 0.261 356.9);        /* #ff1493 - hot pink */
  --cyber-orange: oklch(0.705 0.193 39.2);       /* #ff6b35 - warm orange */
  --cyber-gold: oklch(0.887 0.182 95.3);         /* #ffd700 - gold */

  /* Derived shades (dimmed versions for secondary use) */
  --cyber-pink-dim: oklch(0.400 0.160 356.9);    /* Dimmed pink (same hue, lower L+C) */
  --cyber-orange-dim: oklch(0.450 0.120 39.2);   /* Dimmed orange */
  --cyber-gold-dim: oklch(0.550 0.110 95.3);     /* Dimmed gold */

  /* Surface tones (derived from void bg with slight warmth) */
  --cyber-surface: oklch(0.180 0.008 345.1);     /* Slightly lighter than void */
  --cyber-surface-bright: oklch(0.240 0.010 345.1); /* Card/panel backgrounds */

  /* Text tones */
  --cyber-text: oklch(0.920 0.010 95.3);         /* Warm white (gold-tinted) */
  --cyber-text-dim: oklch(0.600 0.010 95.3);     /* Muted text */
}
```

### Upgraded `cn()` Utility
```typescript
// Source: shadcn/ui manual install docs (ui.shadcn.com/docs/installation/manual)
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

### CyberpunkLayout Skeleton
```tsx
// Progressive enhancement: wraps existing Sidebar + Outlet
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';

export function CyberpunkLayout() {
  return (
    <div className="flex h-screen bg-cyber-void text-cyber-text scanlines">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
```

### `lazy-3d.ts` Utility
```typescript
// Source: React docs (react.dev/reference/react/lazy) + R3F docs (pmndrs/react-three-fiber)
import { lazy, Suspense, type ComponentType, type ReactNode } from 'react';

/**
 * Lazy-load a 3D/heavy component. Wraps React.lazy with proper typing.
 * Use for all R3F, Three.js, and post-processing imports.
 *
 * @example
 * const HeroScene = lazy3D(() => import('./scenes/HeroScene'));
 */
export function lazy3D<P extends Record<string, unknown>>(
  factory: () => Promise<{ default: ComponentType<P> }>,
) {
  return lazy(factory);
}

/**
 * Suspense boundary for 3D content.
 * Provides a consistent loading fallback for all lazy-loaded 3D components.
 */
export function Suspense3D({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  return <Suspense fallback={fallback}>{children}</Suspense>;
}

/*
 * ARCHITECTURE NOTES (for future phases):
 *
 * 1. SINGLE CANVAS STRATEGY
 *    Use ONE <Canvas> at the CyberpunkLayout level.
 *    Never create per-page Canvas components.
 *    Browsers limit WebGL contexts to ~8-16; exceeding this crashes existing contexts.
 *
 * 2. REF-BASED ANIMATION CONVENTION
 *    Inside useFrame(), ALWAYS use useRef to mutate Three.js objects.
 *    NEVER call setState/dispatch inside useFrame() -- it triggers React re-renders at 60fps.
 *
 *    GOOD:
 *      const meshRef = useRef<Mesh>(null);
 *      useFrame((_, delta) => { meshRef.current!.rotation.y += delta; });
 *
 *    BAD:
 *      const [rotation, setRotation] = useState(0);
 *      useFrame((_, delta) => { setRotation(r => r + delta); }); // 60 re-renders/sec!
 *
 * 3. LAZY LOADING
 *    All R3F/Three.js imports MUST go through lazy3D() or dynamic import().
 *    Target: initial bundle under 200KB (Three.js alone is ~500KB gzipped).
 */
```

### vite.config.ts with Path Aliases
```typescript
// Source: shadcn/ui Vite installation docs (ui.shadcn.com/docs/installation/vite)
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8400',
      '/ws': { target: 'ws://localhost:8400', ws: true },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
```

### tsconfig.json with Path Aliases
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### tsconfig.app.json with Path Aliases
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### components.json (shadcn/ui Configuration)
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "radix-nova",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HSL color space for theme vars | oklch color space | Tailwind v4 / shadcn/ui 2024-2025 | Perceptually uniform colors; more vibrant on P3 displays |
| `tailwind.config.js` for theme | `@theme` CSS directive | Tailwind CSS v4 (2024) | No JS config file; theme defined in CSS natively |
| `@layer base { :root { ... } }` | `:root { ... }` outside @layer | Tailwind v4 + shadcn/ui | Variables must NOT be inside `@layer base` for proper cascade |
| shadcn/ui `style: "default"` / `"new-york"` | `style: "radix-nova"` (and others: vega, maia, lyra, mira) | shadcn/ui 2025 | New style system with 5 presets; radix-nova is the recommended default |
| `@apply` for component variants | `class-variance-authority` (CVA) | shadcn/ui standard (2023+) | Type-safe variant management, better than manual `@apply` chains |

**Deprecated/outdated:**
- `tailwind.config.js` / `tailwind.config.ts`: Not needed in Tailwind v4; theme is defined in CSS via `@theme`
- HSL color variables: shadcn/ui now uses oklch by default
- `style: "default"` / `style: "new-york"`: Old shadcn/ui styles replaced by radix-nova/vega/maia/lyra/mira

## Open Questions

1. **Exact oklch dimmed shade values**
   - What we know: Primary palette hex values are locked; oklch conversions computed. Dimmed shades need lower lightness + chroma.
   - What's unclear: The exact dim/bright shade scale (how many steps, what lightness values) will depend on visual testing.
   - Recommendation: Start with the computed values in this research (L * 0.6, C * 0.6 for dim). Adjust during implementation based on visual review. This is within Claude's discretion per CONTEXT.md.

2. **shadcn/ui CLI behavior on existing project**
   - What we know: `npx shadcn@latest init` works on Vite projects. It modifies `index.css` and creates `components.json`.
   - What's unclear: The CLI may overwrite the current `index.css` (which is just `@import "tailwindcss"`). It may also try to modify the `cn()` utility.
   - Recommendation: Run the CLI init first, then layer cyberpunk customizations on top. If the CLI conflicts, use manual installation steps documented above.

3. **`verbatimModuleSyntax` compatibility with `path` import**
   - What we know: `tsconfig.app.json` has `"verbatimModuleSyntax": true`. The shadcn/ui Vite config example uses `import path from "path"` which is a CJS-style default import.
   - What's unclear: This may cause a TypeScript error with `verbatimModuleSyntax`.
   - Recommendation: Use `import * as path from "node:path"` or `import { resolve } from "node:path"` instead if the default import fails.

## Sources

### Primary (HIGH confidence)
- Context7 `/shadcn-ui/ui` - CLI init, components.json, Vite setup, theming, CSS variables
- Context7 `/websites/tailwindcss` - `@theme` directive, oklch color format, custom color definitions, font families
- Context7 `/pmndrs/react-three-fiber` - useFrame ref-based animation, Suspense lazy loading, Canvas setup
- [shadcn/ui Manual Installation](https://ui.shadcn.com/docs/installation/manual) - Complete dependency list, CSS structure, components.json format
- [shadcn/ui Theming](https://ui.shadcn.com/docs/theming) - Full CSS variable list, oklch format, dark mode pattern
- [shadcn/ui Vite Installation](https://ui.shadcn.com/docs/installation/vite) - Step-by-step Vite setup, path aliases, CLI usage
- [shadcn/ui Tailwind v4](https://ui.shadcn.com/docs/tailwind-v4) - `@theme inline` directive, HSL to oklch migration
- [Tailwind CSS v4 Theme Docs](https://tailwindcss.com/docs/theme) - `@theme` directive, custom colors, custom fonts
- [React.lazy Official Docs](https://react.dev/reference/react/lazy) - Lazy loading API, Suspense patterns

### Secondary (MEDIUM confidence)
- [JetBrains Mono on Google Fonts](https://fonts.google.com/specimen/JetBrains+Mono) - Variable font availability confirmed
- [Fontsource JetBrains Mono](https://fontsource.org/fonts/jetbrains-mono/install) - npm package installation, variable font support
- [CRT Scanline CSS Technique](https://aleclownes.com/2017/02/01/crt-display.html) - repeating-linear-gradient pattern
- [Josh W. Comeau backdrop-filter](https://www.joshwcomeau.com/css/backdrop-filter/) - Glassmorphism best practices
- [Glassmorphism CSS Examples](https://freefrontend.com/css-glassmorphism/) - Utility class patterns

### Tertiary (LOW confidence)
- oklch color conversions: Computed programmatically via sRGB -> OKLab -> OKLCH matrix transformation. Values should be validated visually against oklch.com or oklch.fyi before finalizing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - shadcn/ui + Tailwind v4 setup verified via Context7 and official docs; dependency list confirmed from manual install page
- Architecture: HIGH - CSS custom property + `@theme inline` pattern verified across multiple official sources; existing codebase structure fully analyzed
- Pitfalls: HIGH - All pitfalls derived from verified technical constraints (backdrop-filter transparency, pointer-events, webkit prefix, path aliases)
- Color values: MEDIUM - oklch conversions computed mathematically; should be visually validated

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable technologies; shadcn/ui may update styles but core patterns stable)
