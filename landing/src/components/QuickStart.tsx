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
