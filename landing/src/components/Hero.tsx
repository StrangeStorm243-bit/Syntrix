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
              className="flex items-center gap-2 rounded-xl border border-cta-green/40 bg-cta-green/10 px-6 py-3 font-mono text-sm text-cta-green transition-all duration-200 hover:bg-cta-green/20 hover:border-cta-green/60 cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
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
