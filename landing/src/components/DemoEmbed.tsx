"use client";

import { useEffect, useRef } from "react";

export function DemoEmbed() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    const section = sectionRef.current;
    if (!video || !section) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          video.play().catch(() => {
            // Autoplay may be blocked by browser — that's fine
          });
        } else {
          video.pause();
        }
      },
      { threshold: 0.5 },
    );

    observer.observe(section);

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <section ref={sectionRef} className="relative py-24">
      {/* Subtle aurora glow behind the video */}
      <div
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[400px] w-[600px] rounded-full opacity-15 blur-[100px]"
        style={{
          background:
            "radial-gradient(circle, #06B6D4 0%, #3B82F6 40%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-5xl px-6">
        {/* Heading */}
        <div className="mb-12 text-center">
          <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">
            See how Syntrix turns X posts into{" "}
            <span className="bg-gradient-to-r from-aurora-cyan to-aurora-magenta bg-clip-text text-transparent">
              customers
            </span>
          </h2>
          <p className="mt-4 font-body text-lg text-slate-400">
            60 seconds. Zero fluff.
          </p>
        </div>

        {/* Video player */}
        <div className="overflow-hidden rounded-2xl border border-white/10 shadow-2xl shadow-aurora-cyan/5">
          <video
            ref={videoRef}
            src="/demo.mp4"
            muted
            playsInline
            loop
            preload="metadata"
            className="block w-full"
          >
            <track kind="captions" />
          </video>
        </div>

        {/* CTA buttons */}
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <a
            href="https://github.com/StrangeStorm243-bit/Syntrix"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-body text-sm text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
          >
            <span aria-hidden="true">&#11088;</span>
            <span>Star on GitHub</span>
          </a>

          <a
            href="#quickstart"
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-aurora-cyan to-aurora-blue px-6 py-3 font-body text-sm font-semibold text-white transition-all duration-200 hover:opacity-90 focus-visible:ring-2 focus-visible:ring-cyan-400/50 focus-visible:outline-none"
          >
            <span>Get Started</span>
            <span aria-hidden="true">&rarr;</span>
          </a>
        </div>
      </div>
    </section>
  );
}
