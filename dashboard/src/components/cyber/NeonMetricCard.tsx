import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'motion/react';
import { cn } from '../../lib/utils';
import { GlassCard } from './GlassCard';

type NeonColor = 'pink' | 'orange' | 'gold';

interface NeonMetricCardProps {
  title: string;
  value: number;
  icon?: React.ReactNode;
  color?: NeonColor;
  prefix?: string;
  suffix?: string;
  /** @deprecated Use `title` instead */
  label?: string;
  className?: string;
  formatValue?: (n: number) => string;
}

const glowStyles: Record<NeonColor, string> = {
  pink: 'shadow-[0_0_10px_var(--cyber-glow-pink)]',
  orange: 'shadow-[0_0_10px_var(--cyber-glow-orange)]',
  gold: 'shadow-[0_0_10px_var(--cyber-glow-gold)]',
};

const iconStyles: Record<NeonColor, string> = {
  pink: 'text-cyber-pink',
  orange: 'text-cyber-orange',
  gold: 'text-cyber-gold',
};

function defaultFormat(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toString();
}

export function NeonMetricCard({
  title,
  label,
  value,
  icon,
  color = 'pink',
  prefix,
  suffix,
  className,
  formatValue = defaultFormat,
}: NeonMetricCardProps) {
  const displayTitle = title ?? label ?? '';
  const [displayed, setDisplayed] = useState(0);
  const prevValue = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inView = useInView(containerRef, { once: true });

  useEffect(() => {
    if (!inView) return;

    const start = prevValue.current;
    const end = value;
    const duration = 800;
    const startTime = performance.now();
    let raf: number;

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(start + (end - start) * eased));

      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      }
    }

    raf = requestAnimationFrame(tick);
    prevValue.current = end;
    return () => cancelAnimationFrame(raf);
  }, [value, inView]);

  return (
    <GlassCard className={cn(glowStyles[color], className)}>
      <div ref={containerRef} className="flex items-center justify-between">
        <p className="text-sm text-cyber-text-dim">{displayTitle}</p>
        {icon && (
          <motion.span
            className={cn(iconStyles[color], 'drop-shadow-[0_0_6px_currentColor]')}
          >
            {icon}
          </motion.span>
        )}
      </div>
      <p className="mt-2 text-3xl font-bold font-mono text-cyber-text">
        {prefix}
        {formatValue(displayed)}
        {suffix}
      </p>
    </GlassCard>
  );
}
