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
