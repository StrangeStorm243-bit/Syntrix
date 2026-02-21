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
              <div className="group flex w-full flex-col items-center rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-lg transition-all duration-200 hover:bg-white/[0.08] hover:border-white/20">
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
