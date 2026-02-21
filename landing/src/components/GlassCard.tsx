import { type ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function GlassCard({
  children,
  className = "",
  hover = true,
}: GlassCardProps) {
  return (
    <div
      className={`
        rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg
        ${hover ? "transition-colors duration-200 hover:bg-white/[0.08] cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
