# Landing Page "Signal Flow" — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Next.js + Tailwind landing page for Syntrix with aurora gradient cosmos theme, glassmorphic cards, animated pipeline visualization, and terminal showcase.

**Architecture:** Static Next.js site in `landing/` directory at repo root. All components are React Server Components except interactive ones (Navbar scroll, terminal tabs, copy buttons) which use `"use client"`. Aurora gradients are CSS-only for performance. No external state management.

**Tech Stack:** Next.js 15 (App Router), Tailwind CSS 4, TypeScript, Lucide React (icons), next/font (Google Fonts)

**Design doc:** `docs/plans/2026-02-20-landing-page-design.md`
**Design system:** `design-system/syntrix/MASTER.md` + `design-system/syntrix/pages/landing.md`

---

### Task 1: Scaffold Next.js Project

**Files:**
- Create: `landing/package.json`
- Create: `landing/next.config.ts`
- Create: `landing/tailwind.config.ts`
- Create: `landing/postcss.config.mjs`
- Create: `landing/tsconfig.json`
- Create: `landing/src/app/globals.css`
- Create: `landing/src/app/layout.tsx`
- Create: `landing/src/app/page.tsx`

**Step 1: Create Next.js app**

```bash
cd landing/
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm
```

If the directory already exists or interactive prompts are needed, use:

```bash
npx create-next-app@latest landing --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm
```

**Step 2: Install dependencies**

```bash
cd landing/
npm install lucide-react
```

**Step 3: Configure Tailwind for the design system**

Edit `landing/tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#050510",
        "aurora-cyan": "#06B6D4",
        "aurora-magenta": "#D946EF",
        "aurora-blue": "#3B82F6",
        "cta-green": "#22C55E",
      },
      fontFamily: {
        heading: ["var(--font-outfit)", "sans-serif"],
        body: ["var(--font-work-sans)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      maxWidth: {
        "7xl": "1280px",
      },
      animation: {
        "aurora-1": "aurora1 12s ease-in-out infinite",
        "aurora-2": "aurora2 15s ease-in-out infinite",
        "aurora-3": "aurora3 13s ease-in-out infinite",
        "pulse-line": "pulseLine 3s ease-in-out infinite",
      },
      keyframes: {
        aurora1: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(30px, -20px) scale(1.1)" },
          "66%": { transform: "translate(-20px, 15px) scale(0.9)" },
        },
        aurora2: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(-25px, 20px) scale(1.15)" },
          "66%": { transform: "translate(15px, -25px) scale(0.95)" },
        },
        aurora3: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(20px, 25px) scale(1.05)" },
          "66%": { transform: "translate(-30px, -10px) scale(1.1)" },
        },
        pulseLine: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

**Step 4: Set up globals.css with base styles and reduced-motion**

Edit `landing/src/app/globals.css`:

```css
@import "tailwindcss";

@theme {
  --color-base: #050510;
  --color-aurora-cyan: #06B6D4;
  --color-aurora-magenta: #D946EF;
  --color-aurora-blue: #3B82F6;
  --color-cta-green: #22C55E;

  --font-heading: var(--font-outfit), sans-serif;
  --font-body: var(--font-work-sans), sans-serif;
  --font-mono: var(--font-jetbrains-mono), monospace;

  --animate-aurora-1: aurora1 12s ease-in-out infinite;
  --animate-aurora-2: aurora2 15s ease-in-out infinite;
  --animate-aurora-3: aurora3 13s ease-in-out infinite;
  --animate-pulse-line: pulseLine 3s ease-in-out infinite;

  @keyframes aurora1 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(30px, -20px) scale(1.1); }
    66% { transform: translate(-20px, 15px) scale(0.9); }
  }

  @keyframes aurora2 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(-25px, 20px) scale(1.15); }
    66% { transform: translate(15px, -25px) scale(0.95); }
  }

  @keyframes aurora3 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33% { transform: translate(20px, 25px) scale(1.05); }
    66% { transform: translate(-30px, -10px) scale(1.1); }
  }

  @keyframes pulseLine {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
}

@layer base {
  body {
    background-color: var(--color-base);
    color: #F8FAFC;
    font-family: var(--font-body);
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Step 5: Set up layout.tsx with fonts**

Edit `landing/src/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Outfit, Work_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-outfit",
  display: "swap",
});

const workSans = Work_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-work-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Syntrix — Agentic Social Lead Finder",
  description:
    "Open-source CLI that collects tweets, judges relevance via LLM, scores leads, and generates human-approved replies.",
  openGraph: {
    title: "Syntrix — Agentic Social Lead Finder",
    description:
      "Find intent signals. Qualify leads. Draft outreach. Open-source CLI for social lead intelligence.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${workSans.variable} ${jetbrainsMono.variable}`}
    >
      <body className="antialiased">{children}</body>
    </html>
  );
}
```

**Step 6: Create placeholder page.tsx**

Edit `landing/src/app/page.tsx`:

```tsx
export default function Home() {
  return (
    <main className="min-h-screen bg-base">
      <h1 className="text-4xl font-heading font-bold text-center pt-32">
        Syntrix
      </h1>
    </main>
  );
}
```

**Step 7: Verify it runs**

```bash
cd landing && npm run dev
```

Open `http://localhost:3000` — should see "Syntrix" centered on a dark background with Outfit font.

**Step 8: Commit**

```bash
git add landing/
git commit -m "feat: scaffold Next.js landing page with design system config"
```

---

### Task 2: Aurora Background + GlassCard Components

**Files:**
- Create: `landing/src/components/AuroraBackground.tsx`
- Create: `landing/src/components/GlassCard.tsx`

**Step 1: Build AuroraBackground component**

This is the signature visual element — three animated gradient blobs.

Create `landing/src/components/AuroraBackground.tsx`:

```tsx
export function AuroraBackground() {
  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden="true"
    >
      {/* Cyan blob */}
      <div
        className="absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[600px] rounded-full opacity-30 blur-[80px] animate-aurora-1"
        style={{
          background:
            "radial-gradient(circle, #06B6D4 0%, transparent 70%)",
        }}
      />
      {/* Magenta blob */}
      <div
        className="absolute -top-20 left-1/3 h-[400px] w-[500px] rounded-full opacity-25 blur-[80px] animate-aurora-2"
        style={{
          background:
            "radial-gradient(circle, #D946EF 0%, transparent 70%)",
        }}
      />
      {/* Blue blob */}
      <div
        className="absolute top-0 left-2/3 h-[450px] w-[550px] rounded-full opacity-25 blur-[80px] animate-aurora-3"
        style={{
          background:
            "radial-gradient(circle, #3B82F6 0%, transparent 70%)",
        }}
      />
    </div>
  );
}
```

**Step 2: Build GlassCard component**

Create `landing/src/components/GlassCard.tsx`:

```tsx
import { type ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function GlassCard({
  children,
  className = "",
  hover = true,
}: GlassCardProps) {
  return (
    <div
      className={`
        rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg
        ${hover ? "transition-colors duration-200 hover:bg-white/[0.08] cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
```

**Step 3: Verify visually**

Temporarily import AuroraBackground into page.tsx and check the animated blobs render. Then revert page.tsx.

**Step 4: Commit**

```bash
git add landing/src/components/
git commit -m "feat: add AuroraBackground and GlassCard components"
```

---

### Task 3: CodeBlock + TerminalWindow Utility Components

**Files:**
- Create: `landing/src/components/CodeBlock.tsx`
- Create: `landing/src/components/TerminalWindow.tsx`

**Step 1: Build CodeBlock with copy-to-clipboard**

Create `landing/src/components/CodeBlock.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language = "bash" }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative rounded-lg border border-white/10 bg-white/5 font-mono text-sm">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
        <span className="text-xs text-slate-500">{language}</span>
        <button
          onClick={handleCopy}
          className="text-slate-500 hover:text-slate-300 transition-colors duration-200 cursor-pointer"
          aria-label="Copy code"
        >
          {copied ? (
            <Check className="h-4 w-4 text-cta-green" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code className="text-slate-300">{code}</code>
      </pre>
    </div>
  );
}
```

**Step 2: Build TerminalWindow chrome wrapper**

Create `landing/src/components/TerminalWindow.tsx`:

```tsx
import { type ReactNode } from "react";

interface TerminalWindowProps {
  children: ReactNode;
  title?: string;
}

export function TerminalWindow({
  children,
  title = "terminal",
}: TerminalWindowProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg overflow-hidden">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-red-500/70" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
          <div className="h-3 w-3 rounded-full bg-green-500/70" />
        </div>
        <span className="text-xs text-slate-500 font-mono ml-2">
          {title}
        </span>
      </div>
      {/* Terminal body */}
      <div className="p-4 font-mono text-sm leading-relaxed">{children}</div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add landing/src/components/
git commit -m "feat: add CodeBlock and TerminalWindow components"
```

---

### Task 4: Navbar Component

**Files:**
- Create: `landing/src/components/Navbar.tsx`

**Step 1: Build the floating glassmorphic navbar**

Create `landing/src/components/Navbar.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { Copy, Check, Menu, X } from "lucide-react";

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "Pipeline", href: "#pipeline" },
  { label: "Docs", href: "https://github.com/StrangeStorm243-bit/Syntrix#readme" },
  { label: "GitHub", href: "https://github.com/StrangeStorm243-bit/Syntrix" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [copied, setCopied] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleCopy = async () => {
    await navigator.clipboard.writeText("pip install signalops");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <nav
      className={`fixed top-4 left-4 right-4 z-50 rounded-2xl border border-white/10 backdrop-blur-xl transition-colors duration-300 ${
        scrolled ? "bg-black/60" : "bg-white/5"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        {/* Wordmark */}
        <a
          href="#"
          className="font-heading text-sm font-semibold tracking-widest text-white"
        >
          SYNTRIX
        </a>

        {/* Desktop nav links */}
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="font-body text-sm text-slate-400 transition-colors duration-200 hover:text-white"
              {...(link.href.startsWith("http")
                ? { target: "_blank", rel: "noopener noreferrer" }
                : {})}
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Install pill (desktop) */}
        <div className="hidden items-center gap-3 md:flex">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 rounded-lg border border-cta-green/30 bg-cta-green/5 px-3 py-1.5 font-mono text-xs text-cta-green transition-colors duration-200 hover:bg-cta-green/10 cursor-pointer"
          >
            <span>pip install signalops</span>
            {copied ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </button>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="text-slate-400 hover:text-white md:hidden cursor-pointer"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="border-t border-white/5 px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="font-body text-sm text-slate-400 transition-colors duration-200 hover:text-white"
                onClick={() => setMobileOpen(false)}
                {...(link.href.startsWith("http")
                  ? { target: "_blank", rel: "noopener noreferrer" }
                  : {})}
              >
                {link.label}
              </a>
            ))}
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 rounded-lg border border-cta-green/30 bg-cta-green/5 px-3 py-1.5 font-mono text-xs text-cta-green cursor-pointer w-fit"
            >
              <span>pip install signalops</span>
              {copied ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/Navbar.tsx
git commit -m "feat: add floating glassmorphic Navbar with scroll behavior"
```

---

### Task 5: Hero Section

**Files:**
- Create: `landing/src/components/Hero.tsx`

**Step 1: Build hero with aurora background, headline, CTAs, terminal card**

Create `landing/src/components/Hero.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Copy, Check, Github } from "lucide-react";
import { AuroraBackground } from "./AuroraBackground";
import { TerminalWindow } from "./TerminalWindow";

const TERMINAL_LINES = [
  { prefix: "$ ", text: "signalops run all --project spectra", color: "text-white" },
  { prefix: "  ", text: "Query 1/4: \"Code review pain points\" → 47 new tweets", color: "text-slate-400" },
  { prefix: "  ", text: "Query 2/4: \"Bugs slipping through PRs\" → 23 new tweets", color: "text-slate-400" },
  { prefix: "✓ ", text: "Collected 90 tweets (34 duplicates skipped)", color: "text-cta-green" },
  { prefix: "✓ ", text: "Judged: 31 relevant | 52 irrelevant | 7 maybe", color: "text-cta-green" },
  { prefix: "✓ ", text: "Scored 31 leads (top score: 92)", color: "text-cta-green" },
  { prefix: "✓ ", text: "Generated 5 drafts — ready for review", color: "text-cta-green" },
];

export function Hero() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText("pip install signalops");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative min-h-screen overflow-hidden pt-32 pb-16">
      <AuroraBackground />

      <div className="relative z-10 mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center text-center">
          {/* Version badge */}
          <div className="mb-8 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-mono text-slate-400">
            <span className="mr-2 h-1.5 w-1.5 rounded-full bg-cta-green" />
            v0.2 — Open Source
          </div>

          {/* Headline */}
          <h1 className="max-w-4xl font-heading text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
            Find intent signals.{" "}
            <span className="bg-gradient-to-r from-aurora-cyan via-aurora-blue to-aurora-magenta bg-clip-text text-transparent">
              Qualify leads.
            </span>{" "}
            Draft outreach.
          </h1>

          {/* Subheadline */}
          <p className="mt-6 max-w-2xl font-body text-lg text-slate-400 sm:text-xl">
            Open-source CLI that collects tweets, judges relevance via LLM,
            scores leads, and generates human-approved replies.
          </p>

          {/* CTA row */}
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 rounded-xl border border-cta-green/40 bg-cta-green/10 px-6 py-3 font-mono text-sm text-cta-green transition-all duration-200 hover:bg-cta-green/20 hover:border-cta-green/60 cursor-pointer"
            >
              <span>pip install signalops</span>
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>

            <a
              href="https://github.com/StrangeStorm243-bit/Syntrix"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-body text-sm text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white cursor-pointer"
            >
              <Github className="h-4 w-4" />
              <span>View on GitHub</span>
            </a>
          </div>

          {/* Terminal card */}
          <div className="mt-16 w-full max-w-3xl">
            <TerminalWindow title="signalops">
              {TERMINAL_LINES.map((line, i) => (
                <div key={i} className={`${line.color}`}>
                  <span className="text-slate-600">{line.prefix}</span>
                  {line.text}
                </div>
              ))}
            </TerminalWindow>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/Hero.tsx
git commit -m "feat: add Hero section with aurora, headline, CTAs, and terminal demo"
```

---

### Task 6: TrustBar Component

**Files:**
- Create: `landing/src/components/TrustBar.tsx`

**Step 1: Build trust badges strip**

Create `landing/src/components/TrustBar.tsx`:

```tsx
import { Shield, Terminal, Code2 } from "lucide-react";

const BADGES = [
  { icon: Code2, label: "Python 3.11+" },
  { icon: Shield, label: "MIT Licensed" },
  { icon: Terminal, label: "CLI-first" },
];

export function TrustBar() {
  return (
    <section className="border-y border-white/5 py-6">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-6 px-6">
        {BADGES.map((badge) => (
          <div
            key={badge.label}
            className="flex items-center gap-2 rounded-full border border-white/5 px-4 py-1.5 text-xs text-slate-500"
          >
            <badge.icon className="h-3.5 w-3.5" />
            <span className="font-mono">{badge.label}</span>
          </div>
        ))}

        {/* GitHub stars — links to repo */}
        <a
          href="https://github.com/StrangeStorm243-bit/Syntrix"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-full border border-white/5 px-4 py-1.5 text-xs text-slate-500 transition-colors duration-200 hover:text-slate-300 cursor-pointer"
        >
          <img
            src="https://img.shields.io/github/stars/StrangeStorm243-bit/Syntrix?style=flat&color=22C55E&labelColor=0F172A"
            alt="GitHub stars"
            className="h-5"
            loading="lazy"
          />
        </a>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/TrustBar.tsx
git commit -m "feat: add TrustBar with badges and GitHub stars"
```

---

### Task 7: Pipeline Visualization

**Files:**
- Create: `landing/src/components/Pipeline.tsx`

**Step 1: Build the 7-stage pipeline with connecting lines**

Create `landing/src/components/Pipeline.tsx`:

```tsx
import {
  Search,
  FileText,
  Scale,
  BarChart3,
  PenTool,
  CheckCircle2,
  Send,
} from "lucide-react";

const STAGES = [
  {
    icon: Search,
    name: "Collect",
    desc: "Search X for matching tweets",
    gradient: "from-aurora-cyan/20",
  },
  {
    icon: FileText,
    name: "Normalize",
    desc: "Clean text, extract entities",
    gradient: "from-aurora-cyan/15",
  },
  {
    icon: Scale,
    name: "Judge",
    desc: "LLM classifies relevance",
    gradient: "from-aurora-blue/20",
  },
  {
    icon: BarChart3,
    name: "Score",
    desc: "Weighted 0-100 lead ranking",
    gradient: "from-aurora-blue/15",
  },
  {
    icon: PenTool,
    name: "Draft",
    desc: "AI generates reply drafts",
    gradient: "from-aurora-magenta/20",
  },
  {
    icon: CheckCircle2,
    name: "Approve",
    desc: "Human reviews every draft",
    gradient: "from-aurora-magenta/15",
  },
  {
    icon: Send,
    name: "Send",
    desc: "Rate-limited delivery",
    gradient: "from-aurora-magenta/20",
  },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="relative py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            From signal to sent —{" "}
            <span className="bg-gradient-to-r from-aurora-cyan to-aurora-blue bg-clip-text text-transparent">
              in one pipeline
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-400">
            Seven stages, fully configurable, human-approved at every step.
          </p>
        </div>

        {/* Pipeline flow — horizontal desktop, vertical mobile */}
        <div className="flex flex-col items-center gap-4 md:flex-row md:gap-0">
          {STAGES.map((stage, i) => (
            <div key={stage.name} className="flex items-center md:flex-1">
              {/* Stage card */}
              <div className="group flex w-full flex-col items-center rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-lg transition-all duration-200 hover:bg-white/[0.08] hover:border-white/20 cursor-pointer">
                <div
                  className={`mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${stage.gradient} to-transparent`}
                >
                  <stage.icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="font-heading text-sm font-semibold text-white">
                  {stage.name}
                </h3>
                <p className="mt-1 text-center font-body text-xs text-slate-500">
                  {stage.desc}
                </p>
              </div>

              {/* Connecting line (not after last) */}
              {i < STAGES.length - 1 && (
                <>
                  {/* Desktop: horizontal line */}
                  <div className="hidden h-px w-8 flex-shrink-0 bg-gradient-to-r from-white/20 to-white/5 md:block" />
                  {/* Mobile: vertical line */}
                  <div className="h-4 w-px bg-gradient-to-b from-white/20 to-white/5 md:hidden" />
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/Pipeline.tsx
git commit -m "feat: add Pipeline visualization with 7 connected stages"
```

---

### Task 8: Features Grid

**Files:**
- Create: `landing/src/components/Features.tsx`

**Step 1: Build 2x3 feature grid**

Create `landing/src/components/Features.tsx`:

```tsx
import {
  Brain,
  BarChart3,
  Sparkles,
  UserCheck,
  Gauge,
  Target,
} from "lucide-react";
import { GlassCard } from "./GlassCard";

const FEATURES = [
  {
    icon: Brain,
    title: "LLM-Powered Judging",
    desc: "Claude or GPT classifies tweet relevance with structured confidence scores and reasoning.",
    gradient: "from-aurora-cyan to-aurora-blue",
  },
  {
    icon: BarChart3,
    title: "Weighted Lead Scoring",
    desc: "0-100 score combining relevance, author authority, engagement, recency, and intent strength.",
    gradient: "from-aurora-blue to-aurora-magenta",
  },
  {
    icon: Sparkles,
    title: "AI Draft Generation",
    desc: "Context-aware reply drafts using your project persona, tone, and voice guidelines.",
    gradient: "from-aurora-magenta to-aurora-cyan",
  },
  {
    icon: UserCheck,
    title: "Human-in-the-Loop",
    desc: "Approve, edit, or reject every single draft before it's sent. No auto-pilot.",
    gradient: "from-aurora-cyan to-aurora-blue",
  },
  {
    icon: Gauge,
    title: "Rate-Limited Sending",
    desc: "Configurable hourly, daily, and monthly caps with jitter. Compliance-first design.",
    gradient: "from-aurora-blue to-aurora-magenta",
  },
  {
    icon: Target,
    title: "Outcome Tracking",
    desc: "Monitor if your replies get liked, replied to, or lead to follows and conversions.",
    gradient: "from-aurora-magenta to-aurora-cyan",
  },
];

export function Features() {
  return (
    <section id="features" className="relative py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            Built for{" "}
            <span className="bg-gradient-to-r from-aurora-blue to-aurora-magenta bg-clip-text text-transparent">
              founders and growth teams
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-400">
            Everything you need to find high-intent leads and engage them
            intelligently.
          </p>
        </div>

        {/* 2x3 grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feat) => (
            <GlassCard key={feat.title} className="p-6">
              <div
                className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${feat.gradient} opacity-80`}
              >
                <feat.icon className="h-5 w-5 text-white" />
              </div>
              <h3 className="font-heading text-base font-semibold text-white">
                {feat.title}
              </h3>
              <p className="mt-2 font-body text-sm leading-relaxed text-slate-400">
                {feat.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/Features.tsx
git commit -m "feat: add 2x3 Features grid with glassmorphic cards"
```

---

### Task 9: Terminal Showcase (Tabbed)

**Files:**
- Create: `landing/src/components/TerminalShowcase.tsx`

**Step 1: Build tabbed terminal demo**

Create `landing/src/components/TerminalShowcase.tsx`:

```tsx
"use client";

import { useState } from "react";
import { TerminalWindow } from "./TerminalWindow";

interface TerminalTab {
  label: string;
  command: string;
  lines: { text: string; color?: string }[];
}

const TABS: TerminalTab[] = [
  {
    label: "run all",
    command: "signalops run all --project spectra",
    lines: [
      { text: "⠋ Collecting tweets..." },
      { text: '  Query 1/4: "Code review pain points" → 47 new tweets' },
      { text: '  Query 2/4: "Bugs slipping through PRs" → 23 new tweets' },
      { text: "✓ Collected 90 tweets (34 duplicates skipped)", color: "text-cta-green" },
      { text: "" },
      { text: "⠋ Judging relevance..." },
      { text: "  Relevant: 31 | Irrelevant: 52 | Maybe: 7" },
      { text: "✓ Judged 90 tweets (avg confidence: 0.84)", color: "text-cta-green" },
      { text: "" },
      { text: "✓ Scored 31 relevant tweets", color: "text-cta-green" },
      { text: "  Top lead: @techleadSara (score: 92)" },
    ],
  },
  {
    label: "queue list",
    command: "signalops queue list",
    lines: [
      { text: "┌────┬───────┬────────────────┬──────────────────────────────────────┬────────┐" },
      { text: "│ ID │ Score │ Reply To       │ Draft                                │ Status │" },
      { text: "├────┼───────┼────────────────┼──────────────────────────────────────┼────────┤" },
      { text: '│ 1  │ 92    │ @techleadSara  │ "Totally feel that — we built..."    │ pending│', color: "text-aurora-cyan" },
      { text: '│ 2  │ 87    │ @devops_mike   │ "Great question — we\'ve been..."    │ pending│', color: "text-aurora-cyan" },
      { text: '│ 3  │ 83    │ @ctojennifer   │ "That\'s frustrating. We catch..."   │ pending│', color: "text-aurora-cyan" },
      { text: "└────┴───────┴────────────────┴──────────────────────────────────────┴────────┘" },
    ],
  },
  {
    label: "stats",
    command: "signalops stats",
    lines: [
      { text: "┌──────────────────────────────────────┐" },
      { text: "│ Spectra AI — Pipeline Stats          │", color: "text-white font-semibold" },
      { text: "├──────────────────────────────────────┤" },
      { text: "│ Collected:      1,247 tweets         │" },
      { text: "│ Judged:         1,247 (100%)         │" },
      { text: "│   Relevant:       389 (31.2%)        │", color: "text-cta-green" },
      { text: "│   Irrelevant:     798 (64.0%)        │" },
      { text: "│ Scored:           389                │" },
      { text: "│   Avg score:      62.4               │" },
      { text: "│ Drafted:          87                 │" },
      { text: "│ Approved:         64 (73.6%)         │", color: "text-cta-green" },
      { text: "│ Sent:             58                 │", color: "text-cta-green" },
      { text: "└──────────────────────────────────────┘" },
    ],
  },
];

export function TerminalShowcase() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <section className="py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-16 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            See it{" "}
            <span className="bg-gradient-to-r from-aurora-cyan to-aurora-magenta bg-clip-text text-transparent">
              in action
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-400">
            Real CLI output from the Syntrix pipeline.
          </p>
        </div>

        <div className="mx-auto max-w-3xl">
          {/* Tabs */}
          <div className="mb-4 flex gap-2" role="tablist">
            {TABS.map((tab, i) => (
              <button
                key={tab.label}
                role="tab"
                aria-selected={activeTab === i}
                onClick={() => setActiveTab(i)}
                className={`rounded-lg px-4 py-2 font-mono text-xs transition-colors duration-200 cursor-pointer ${
                  activeTab === i
                    ? "bg-white/10 text-white border border-white/20"
                    : "text-slate-500 hover:text-slate-300 border border-transparent"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Terminal */}
          <TerminalWindow title={TABS[activeTab].command}>
            <div className="text-slate-400">
              <div className="text-white">
                $ {TABS[activeTab].command}
              </div>
              {TABS[activeTab].lines.map((line, i) => (
                <div key={i} className={line.color || "text-slate-400"}>
                  {line.text || "\u00A0"}
                </div>
              ))}
            </div>
          </TerminalWindow>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/TerminalShowcase.tsx
git commit -m "feat: add tabbed TerminalShowcase with run/queue/stats demos"
```

---

### Task 10: QuickStart Section

**Files:**
- Create: `landing/src/components/QuickStart.tsx`

**Step 1: Build 3-step quick start**

Create `landing/src/components/QuickStart.tsx`:

```tsx
import { GlassCard } from "./GlassCard";
import { CodeBlock } from "./CodeBlock";

const STEPS = [
  {
    number: 1,
    title: "Install",
    desc: "One command via PyPI.",
    code: "pip install signalops",
  },
  {
    number: 2,
    title: "Configure",
    desc: "Set your API keys.",
    code: "export ANTHROPIC_API_KEY=sk-...\nexport X_BEARER_TOKEN=AAAA...",
  },
  {
    number: 3,
    title: "Run",
    desc: "Execute the full pipeline.",
    code: "signalops project set spectra\nsignalops run all --dry-run",
  },
];

export function QuickStart() {
  return (
    <section className="relative py-24">
      {/* Magenta aurora accent at bottom */}
      <div
        className="pointer-events-none absolute bottom-0 left-1/2 -translate-x-1/2 h-[300px] w-[500px] rounded-full opacity-15 blur-[80px]"
        style={{
          background: "radial-gradient(circle, #D946EF 0%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-7xl px-6">
        <div className="mb-16 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            Get started in{" "}
            <span className="bg-gradient-to-r from-aurora-magenta to-aurora-cyan bg-clip-text text-transparent">
              60 seconds
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-400">
            Three steps from zero to your first pipeline run.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((step) => (
            <GlassCard key={step.number} className="p-6" hover={false}>
              <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-aurora-magenta/30 to-aurora-cyan/30 font-heading text-sm font-bold text-white">
                {step.number}
              </div>
              <h3 className="font-heading text-lg font-semibold text-white">
                {step.title}
              </h3>
              <p className="mt-1 mb-4 font-body text-sm text-slate-400">
                {step.desc}
              </p>
              <CodeBlock code={step.code} />
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/QuickStart.tsx
git commit -m "feat: add QuickStart section with 3 numbered steps"
```

---

### Task 11: Footer

**Files:**
- Create: `landing/src/components/Footer.tsx`

**Step 1: Build minimal dark footer**

Create `landing/src/components/Footer.tsx`:

```tsx
import { Github } from "lucide-react";

const LINKS = [
  { label: "GitHub", href: "https://github.com/StrangeStorm243-bit/Syntrix" },
  { label: "PyPI", href: "https://pypi.org/project/signalops/" },
  { label: "Docs", href: "https://github.com/StrangeStorm243-bit/Syntrix#readme" },
  { label: "Architecture", href: "https://github.com/StrangeStorm243-bit/Syntrix/blob/main/PLANA.md" },
];

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-6 px-6 sm:flex-row sm:justify-between">
        {/* Wordmark */}
        <div className="flex items-center gap-3">
          <span className="font-heading text-sm font-semibold tracking-widest text-slate-500">
            SYNTRIX
          </span>
          <span className="text-xs text-slate-600">MIT License</span>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6">
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm text-slate-500 transition-colors duration-200 hover:text-slate-300 cursor-pointer"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Credit */}
        <p className="text-xs text-slate-600">
          Built with Claude &amp; GPT
        </p>
      </div>
    </footer>
  );
}
```

**Step 2: Commit**

```bash
git add landing/src/components/Footer.tsx
git commit -m "feat: add minimal Footer with links"
```

---

### Task 12: Assemble All Sections in page.tsx

**Files:**
- Modify: `landing/src/app/page.tsx`

**Step 1: Import all sections and assemble**

Edit `landing/src/app/page.tsx`:

```tsx
import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { TrustBar } from "@/components/TrustBar";
import { Pipeline } from "@/components/Pipeline";
import { Features } from "@/components/Features";
import { TerminalShowcase } from "@/components/TerminalShowcase";
import { QuickStart } from "@/components/QuickStart";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="bg-base">
        <Hero />
        <TrustBar />
        <Pipeline />
        <Features />
        <TerminalShowcase />
        <QuickStart />
      </main>
      <Footer />
    </>
  );
}
```

**Step 2: Run dev server and verify all sections render**

```bash
cd landing && npm run dev
```

Open `http://localhost:3000` and verify:
- [ ] Navbar floats with glassmorphic effect, copy button works
- [ ] Hero shows aurora blobs animating, headline gradient renders, terminal card visible
- [ ] Trust bar shows badges
- [ ] Pipeline shows 7 connected stages
- [ ] Features grid shows 6 cards with hover effects
- [ ] Terminal showcase tabs switch between outputs
- [ ] Quick start shows 3 numbered steps with copyable code
- [ ] Footer renders with links
- [ ] Mobile responsive at 375px

**Step 3: Commit**

```bash
git add landing/src/app/page.tsx
git commit -m "feat: assemble all sections into landing page"
```

---

### Task 13: Polish, Accessibility Audit, and Final Cleanup

**Files:**
- Modify: Various components as needed

**Step 1: Run accessibility checks**

- Verify all `cursor-pointer` on clickable elements
- Verify all `aria-label` on icon-only buttons
- Verify focus rings visible (`ring-2 ring-cyan-400/50` on focus-visible)
- Verify `prefers-reduced-motion` stops all animations
- Verify tab order matches visual order
- Check text contrast ratios: `#F8FAFC` on `#050510` = 19.2:1 (passes AAA)

**Step 2: Run build to check for errors**

```bash
cd landing && npm run build
```

Fix any TypeScript or build errors.

**Step 3: Run Lighthouse audit**

```bash
cd landing && npm run build && npm run start
```

Open Chrome DevTools > Lighthouse > Performance + Accessibility. Target 95+ on both.

**Step 4: Final commit**

```bash
git add landing/
git commit -m "feat: polish landing page accessibility and performance"
```

---

### Task 14: Add .gitignore and Documentation

**Files:**
- Create: `landing/.gitignore`
- Modify: `landing/README.md` (if created by create-next-app)

**Step 1: Ensure proper gitignore**

Create `landing/.gitignore`:

```
node_modules/
.next/
out/
.env*.local
```

**Step 2: Commit**

```bash
git add landing/.gitignore
git commit -m "chore: add landing page gitignore"
```
