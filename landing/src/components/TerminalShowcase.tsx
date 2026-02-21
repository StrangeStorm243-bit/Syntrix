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
                className={`rounded-lg px-4 py-2 font-mono text-xs transition-colors duration-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none ${
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
