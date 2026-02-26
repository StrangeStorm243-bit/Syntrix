"use client";

import { useState, useEffect } from "react";
import { Copy, Check, Menu, X } from "lucide-react";

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "Pipeline", href: "#pipeline" },
  { label: "Docs", href: "https://github.com/StrangeStorm243-bit/Syntrix#readme" },
  { label: "GitHub", href: "https://github.com/StrangeStorm243-bit/Syntrix" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [copied, setCopied] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleCopy = async () => {
    await navigator.clipboard.writeText("docker compose up");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <nav
      className={`fixed top-4 left-4 right-4 z-50 rounded-2xl border border-white/10 backdrop-blur-xl transition-colors duration-300 ${
        scrolled ? "bg-black/60" : "bg-white/5"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        {/* Wordmark */}
        <a
          href="#"
          className="font-heading text-sm font-semibold tracking-widest text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none rounded-sm"
        >
          SYNTRIX
        </a>

        {/* Desktop nav links */}
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="font-body text-sm text-slate-400 transition-colors duration-200 hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none rounded-sm"
              {...(link.href.startsWith("http")
                ? { target: "_blank", rel: "noopener noreferrer" }
                : {})}
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Install pill (desktop) */}
        <div className="hidden items-center gap-3 md:flex">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 rounded-lg border border-cta-green/30 bg-cta-green/5 px-3 py-1.5 font-mono text-xs text-cta-green transition-colors duration-200 hover:bg-cta-green/10 cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
          >
            <span>docker compose up</span>
            {copied ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </button>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="text-slate-400 hover:text-white md:hidden cursor-pointer focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none rounded-sm"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="border-t border-white/5 px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="font-body text-sm text-slate-400 transition-colors duration-200 hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none rounded-sm"
                onClick={() => setMobileOpen(false)}
                {...(link.href.startsWith("http")
                  ? { target: "_blank", rel: "noopener noreferrer" }
                  : {})}
              >
                {link.label}
              </a>
            ))}
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 rounded-lg border border-cta-green/30 bg-cta-green/5 px-3 py-1.5 font-mono text-xs text-cta-green cursor-pointer w-fit focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
            >
              <span>docker compose up</span>
              {copied ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
