import { type ReactNode } from "react";

interface TerminalWindowProps {
  children: ReactNode;
  title?: string;
}

export function TerminalWindow({
  children,
  title = "terminal",
}: TerminalWindowProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg overflow-hidden">
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-red-500/70" />
          <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
          <div className="h-3 w-3 rounded-full bg-green-500/70" />
        </div>
        <span className="text-xs text-slate-500 font-mono ml-2">
          {title}
        </span>
      </div>
      {/* Terminal body */}
      <div className="p-4 font-mono text-sm leading-relaxed">{children}</div>
    </div>
  );
}
