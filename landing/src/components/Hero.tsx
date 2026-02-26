"use client";

import { useState, lazy, Suspense } from "react";
import { Copy, Check, Github } from "lucide-react";
import { AuroraBackground } from "./AuroraBackground";
import { TerminalWindow } from "./TerminalWindow";

const HeroScene = lazy(() =>
  import("./HeroScene").then((m) => ({ default: m.HeroScene }))
);

const TERMINAL_LINES = [
  { prefix: "$ ", text: "git clone https://github.com/StrangeStorm243-bit/Syntrix.git", color: "text-white" },
  { prefix: "$ ", text: "cd Syntrix && docker compose up", color: "text-white" },
  { prefix: "  ", text: "✓ api — FastAPI on port 8400", color: "text-cta-green" },
  { prefix: "  ", text: "✓ dashboard — React UI on port 3000", color: "text-cta-green" },
  { prefix: "  ", text: "✓ ollama — Local LLM ready (llama3.2 + mistral)", color: "text-cta-green" },
  { prefix: "  ", text: "", color: "text-slate-400" },
  { prefix: "  ", text: "Open http://localhost:3000 → Setup wizard guides you through.", color: "text-aurora-cyan" },
];

export function Hero() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText("git clone https://github.com/StrangeStorm243-bit/Syntrix.git && cd Syntrix && docker compose up");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative min-h-screen overflow-hidden pt-32 pb-16">
      <AuroraBackground />
      <Suspense fallback={null}>
        <HeroScene />
      </Suspense>

      <div className="relative z-10 mx-auto max-w-7xl px-6 pointer-events-none">
        <div className="flex flex-col items-center text-center [&_button]:pointer-events-auto [&_a]:pointer-events-auto">
          {/* Version badge */}
          <div className="mb-8 inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-mono text-slate-400">
            <span className="mr-2 h-1.5 w-1.5 rounded-full bg-cta-green" />
            v0.3 — Open Source
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
            Open-source lead finder that collects tweets, judges relevance via LLM,
            scores leads, drafts outreach, and sends DMs — all from a self-hosted dashboard.
          </p>

          {/* CTA row */}
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 rounded-xl border border-cta-green/40 bg-cta-green/10 px-6 py-3 font-mono text-sm text-cta-green transition-all duration-200 hover:bg-cta-green/20 hover:border-cta-green/60 cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
            >
              <span>docker compose up</span>
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
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-body text-sm text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
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
