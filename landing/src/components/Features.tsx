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
