# Landing Page Design — "Signal Flow"

> **Date:** 2026-02-20
> **Status:** Approved
> **Stack:** Next.js + Tailwind CSS
> **Theme:** Aurora Gradient Cosmos — "Signal Flow" variant

---

## Concept

The pipeline IS the visual story. An animated aurora gradient flows across the page like data flowing through the pipeline stages (Collect -> Judge -> Score -> Draft -> Send). Each page section corresponds to a pipeline stage, with the aurora morphing color as you scroll — cyan (collect) through blue (judge/score) to magenta (draft/send).

**Goal:** Open-source adoption + product showcase. Drive GitHub stars, pip installs, and docs visits. No waitlist, no SaaS conversion (yet).

---

## Design System

### Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-base` | `#050510` | Page background (true dark) |
| `--aurora-cyan` | `#06B6D4` | Aurora blob 1, collect stage |
| `--aurora-magenta` | `#D946EF` | Aurora blob 2, draft/send stage |
| `--aurora-blue` | `#3B82F6` | Aurora blob 3, judge/score stage |
| `--cta-green` | `#22C55E` | Terminal green, primary CTA borders |
| `--text-primary` | `#F8FAFC` | Headlines, primary text |
| `--text-secondary` | `#94A3B8` | Subheadlines, descriptions |
| `--text-muted` | `#64748B` | Badges, labels, footer |
| `--glass-bg` | `rgba(255,255,255,0.05)` | Card backgrounds |
| `--glass-border` | `rgba(255,255,255,0.10)` | Card borders |
| `--glass-bg-hover` | `rgba(255,255,255,0.08)` | Card hover state |

### Typography

| Role | Font | Weights | Usage |
|------|------|---------|-------|
| Headings | Outfit | 400, 500, 600, 700 | All headings, hero, section titles |
| Body | Work Sans | 300, 400, 500, 600 | Descriptions, paragraphs, nav links |
| Code | JetBrains Mono | 400, 500, 600 | Terminal output, code blocks, badges |

Google Fonts import:
```
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Work+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

### Spacing & Layout

- Max content width: `max-w-7xl` (1280px)
- Section padding: `py-24` desktop, `py-16` mobile
- Card border radius: `rounded-2xl`
- Navbar: floating with `top-4 left-4 right-4` spacing
- Breakpoints: 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide)

### Effects

- Aurora blobs: CSS radial gradients + `filter: blur(80px)` + `@keyframes` 12-15s loop
- Glass cards: `backdrop-blur-lg` + `bg-white/5` + `border border-white/10`
- Micro-interactions: 200-300ms transitions on hover/focus
- Code typing animation: CSS steps() or JS typewriter in hero terminal
- Pipeline connecting lines: gradient animation left-to-right pulse
- `prefers-reduced-motion`: disable all animations, show static gradients
- Icons: Lucide React (consistent icon set, no emojis)

---

## Section-by-Section Spec

### S1: Navigation Bar

- **Type:** Fixed, floating glassmorphic
- **Left:** "SYNTRIX" wordmark — Outfit SemiBold, tracking-wide, text-sm
- **Center:** Feature links — Features | Pipeline | Docs | GitHub
- **Right:** `pip install signalops` code pill (copy icon) + GitHub star badge
- **Scroll behavior:** Gains `bg-black/60` tint on scroll for readability
- **Mobile:** Hamburger menu with slide-out drawer

### S2: Hero

- **Background:** True black + 3 aurora gradient blobs (cyan, magenta, blue) in upper-center, animated 12-15s morph loop
- **Aurora implementation:** Three absolutely-positioned divs with radial-gradient, filter: blur(80px), animated translateX/Y and scale
- **Layout:** Center-aligned, stacked, `min-h-screen`, `pt-32`
- **Content:**
  1. Version badge pill: "v0.2 — Open Source" with subtle glow border
  2. Headline: "Find intent signals. Qualify leads. Draft outreach." — Outfit Bold, 56px desktop / 36px mobile
  3. Subheadline: "Open-source CLI that collects tweets, judges relevance via LLM, scores leads, and generates human-approved replies." — Work Sans Regular, 20px, text-slate-400
  4. CTA row:
     - Primary: `pip install signalops` — code pill, green border (#22C55E), copy-to-clipboard
     - Secondary: `View on GitHub` — outline button, GitHub icon + live star count
  5. Terminal card: Glassmorphic card showing `signalops run all` output with green checkmarks, typing animation on load

### S3: Trust Bar

- **Position:** Below hero, horizontal centered strip
- **Content:** GitHub stars badge | "MIT Licensed" | "Python 3.11+" | "CLI-first"
- **Style:** Small pills, text-slate-500, border-white/5, inline-flex with gap-4

### S4: Pipeline Visualization

- **Aurora shift:** Cyan -> Blue transition
- **Headline:** "From signal to sent — in one pipeline"
- **Layout:** Horizontal scrollable flow on desktop, vertical stack on mobile
- **7 pipeline cards:** Collect -> Normalize -> Judge -> Score -> Draft -> Approve -> Send
  - Each: Lucide icon, stage name (Outfit SemiBold), one-line description (Work Sans)
  - Glassmorphic cards with aurora-tinted glow on hover
- **Connecting lines:** Gradient-animated lines between cards, pulsing left-to-right

### S5: Features Grid

- **Aurora shift:** Blue -> Blue-magenta blend
- **Headline:** "Built for founders and growth teams"
- **Layout:** 2x3 responsive grid (3 cols desktop, 2 cols tablet, 1 col mobile)
- **6 feature cards:**
  1. LLM-Powered Judging — Claude or GPT classifies relevance with confidence scores
  2. Weighted Lead Scoring — 0-100 score combining relevance, authority, engagement, recency, intent
  3. AI Draft Generation — Context-aware replies using project persona and tone
  4. Human-in-the-Loop — Approve, edit, or reject every draft before it's sent
  5. Rate-Limited Sending — Configurable hourly/daily caps with jitter
  6. Outcome Tracking — Monitor if replies get liked, replied to, or followed
- **Card style:** Glassmorphic, Lucide icon with aurora-gradient fill, hover glow

### S6: Terminal Showcase

- **Headline:** "See it in action"
- **Layout:** Tabbed terminal window
- **Tabs:**
  1. `signalops run all` — full pipeline output
  2. `signalops queue list` — approval queue table
  3. `signalops stats` — stats dashboard
- **Style:** Dark terminal window with title bar dots, JetBrains Mono, syntax coloring (green success, cyan data, white text)

### S7: Quick Start

- **Aurora shift:** Warm magenta (end of pipeline = action)
- **Headline:** "Get started in 60 seconds"
- **Layout:** 3 numbered step cards, horizontal on desktop, vertical on mobile
- **Steps:**
  1. Install: `pip install signalops`
  2. Configure: `export ANTHROPIC_API_KEY=... && export X_BEARER_TOKEN=...`
  3. Run: `signalops project set spectra && signalops run all --dry-run`
- **Card style:** Glassmorphic with number badge, description, copyable code block

### S8: Footer

- **Style:** Minimal, dark, border-t border-white/5
- **Content:**
  - SYNTRIX wordmark
  - Link columns: GitHub | PyPI | Docs | Architecture
  - "Built with Claude & GPT" subtle credit
  - MIT License note

---

## Accessibility

- All text meets WCAG AA 4.5:1 contrast on dark background
- Focus rings visible on all interactive elements (ring-2 ring-cyan-400)
- Tab order matches visual order
- prefers-reduced-motion disables all animations, shows static gradient
- Alt text on all icons (aria-label for icon-only buttons)
- Semantic HTML: nav, main, section, footer
- Keyboard navigable tabs in terminal showcase

## Performance

- Fonts: `display=swap` to prevent FOIT
- Aurora: CSS-only animation (no canvas/WebGL), hardware-accelerated transforms
- Images: None in initial design (pure CSS + SVG icons)
- Code splitting: Next.js automatic
- Target: Lighthouse 95+ on all metrics

---

## File Structure (Next.js)

```
landing/
├── package.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── tsconfig.json
├── public/
│   └── favicon.ico
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with fonts + metadata
│   │   ├── page.tsx            # Main landing page (assembles sections)
│   │   └── globals.css         # Tailwind base + aurora keyframes + custom utilities
│   └── components/
│       ├── Navbar.tsx           # Floating glassmorphic nav
│       ├── Hero.tsx             # Aurora background + headline + terminal card
│       ├── AuroraBackground.tsx # Reusable aurora gradient mesh
│       ├── TrustBar.tsx         # Badges strip
│       ├── Pipeline.tsx         # 7-stage pipeline visualization
│       ├── Features.tsx         # 2x3 feature grid
│       ├── TerminalShowcase.tsx # Tabbed terminal demo
│       ├── QuickStart.tsx       # 3-step getting started
│       ├── Footer.tsx           # Minimal footer
│       ├── GlassCard.tsx        # Reusable glassmorphic card
│       ├── CodeBlock.tsx        # Styled code block with copy
│       └── TerminalWindow.tsx   # Terminal chrome wrapper
```
