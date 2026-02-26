import {
  Search,
  FileText,
  Scale,
  BarChart3,
  PenTool,
  CheckCircle2,
  Send,
  MessageCircle,
} from "lucide-react";

const STAGES = [
  {
    icon: Search,
    name: "Collect",
    desc: "Search X for matching tweets",
    color: "text-cyan-600",
    bg: "bg-cyan-50",
    border: "border-cyan-200",
  },
  {
    icon: FileText,
    name: "Normalize",
    desc: "Clean text, extract entities",
    color: "text-cyan-500",
    bg: "bg-cyan-50/50",
    border: "border-cyan-100",
  },
  {
    icon: Scale,
    name: "Judge",
    desc: "LLM classifies relevance",
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  {
    icon: BarChart3,
    name: "Score",
    desc: "Weighted 0-100 lead ranking",
    color: "text-blue-500",
    bg: "bg-blue-50/50",
    border: "border-blue-100",
  },
  {
    icon: PenTool,
    name: "Draft",
    desc: "AI generates reply drafts",
    color: "text-purple-600",
    bg: "bg-purple-50",
    border: "border-purple-200",
  },
  {
    icon: CheckCircle2,
    name: "Approve",
    desc: "Human reviews every draft",
    color: "text-purple-500",
    bg: "bg-purple-50/50",
    border: "border-purple-100",
  },
  {
    icon: Send,
    name: "Send",
    desc: "Rate-limited delivery",
    color: "text-fuchsia-600",
    bg: "bg-fuchsia-50",
    border: "border-fuchsia-200",
  },
  {
    icon: MessageCircle,
    name: "DM",
    desc: "Direct message outreach",
    color: "text-fuchsia-700",
    bg: "bg-fuchsia-50",
    border: "border-fuchsia-200",
  },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="bg-white py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="font-heading text-3xl font-bold text-slate-900 sm:text-4xl">
            From signal to sent —{" "}
            <span className="bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              in one pipeline
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-500">
            Eight stages, fully configurable, human-approved at every step.
          </p>
        </div>

        {/* Pipeline flow — horizontal desktop, vertical mobile */}
        <div className="flex flex-col items-center gap-4 md:flex-row md:gap-0">
          {STAGES.map((stage, i) => (
            <div key={stage.name} className="flex items-center md:flex-1">
              {/* Stage card */}
              <div className={`group flex w-full flex-col items-center rounded-2xl border ${stage.border} bg-white p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:border-slate-300`}>
                <div
                  className={`mb-3 flex h-12 w-12 items-center justify-center rounded-xl ${stage.bg}`}
                >
                  <stage.icon className={`h-6 w-6 ${stage.color}`} />
                </div>
                <h3 className="font-heading text-sm font-semibold text-slate-900">
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
                  <div className="hidden h-px w-8 flex-shrink-0 bg-gradient-to-r from-slate-300 to-slate-200 md:block" />
                  {/* Mobile: vertical line */}
                  <div className="h-4 w-px bg-gradient-to-b from-slate-300 to-slate-200 md:hidden" />
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
