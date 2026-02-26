export function GetStartedCTA() {
  return (
    <section className="relative overflow-hidden bg-base py-16">
      {/* Gradient accent */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(6,182,212,0.08) 0%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-3xl px-6 text-center">
        <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
          Ready to find your next{" "}
          <span className="bg-gradient-to-r from-aurora-cyan to-aurora-magenta bg-clip-text text-transparent">
            customers
          </span>
          ?
        </h2>
        <p className="mt-4 font-body text-lg text-slate-400">
          Three commands. Sixty seconds. Zero cold emails.
        </p>
        <a
          href="#quickstart"
          className="mt-8 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-aurora-cyan to-aurora-magenta px-8 py-3 font-heading text-sm font-semibold text-white shadow-lg shadow-aurora-cyan/20 transition-all duration-200 hover:shadow-xl hover:shadow-aurora-cyan/30 hover:-translate-y-0.5"
        >
          Get Started
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 5v14" />
            <path d="m19 12-7 7-7-7" />
          </svg>
        </a>
      </div>
    </section>
  );
}
