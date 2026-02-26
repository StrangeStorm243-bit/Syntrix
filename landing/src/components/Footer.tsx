const LINKS = [
  { label: "GitHub", href: "https://github.com/StrangeStorm243-bit/Syntrix" },
  { label: "PyPI", href: "https://pypi.org/project/signalops/" },
  { label: "Docs", href: "https://github.com/StrangeStorm243-bit/Syntrix#readme" },
  { label: "Dashboard", href: "https://github.com/StrangeStorm243-bit/Syntrix#web-dashboard" },
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
          <span className="text-xs text-slate-600">AGPL-3.0 License</span>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6">
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-sm text-slate-500 transition-colors duration-200 hover:text-slate-300 cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none rounded-sm"
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
