import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

type NeonBadgeVariant = 'pink' | 'orange' | 'gold' | 'green' | 'red';

interface NeonBadgeProps {
  children: React.ReactNode;
  variant?: NeonBadgeVariant;
  glow?: boolean;
  className?: string;
}

const variantStyles: Record<NeonBadgeVariant, string> = {
  pink: 'text-cyber-pink border-cyber-pink',
  orange: 'text-cyber-orange border-cyber-orange',
  gold: 'text-cyber-gold border-cyber-gold',
  green: 'text-emerald-400 border-emerald-400',
  red: 'text-red-400 border-red-400',
};

const glowStyles: Record<NeonBadgeVariant, string> = {
  pink: 'shadow-[0_0_8px_var(--cyber-glow-pink)]',
  orange: 'shadow-[0_0_8px_var(--cyber-glow-orange)]',
  gold: 'shadow-[0_0_8px_var(--cyber-glow-gold)]',
  green: 'shadow-[0_0_8px_oklch(0.792_0.209_151.711_/_0.4)]',
  red: 'shadow-[0_0_8px_oklch(0.637_0.237_25.331_/_0.4)]',
};

const glowAnimation: Record<NeonBadgeVariant, string[]> = {
  pink: [
    '0 0 4px var(--cyber-glow-pink)',
    '0 0 12px var(--cyber-glow-pink)',
    '0 0 4px var(--cyber-glow-pink)',
  ],
  orange: [
    '0 0 4px var(--cyber-glow-orange)',
    '0 0 12px var(--cyber-glow-orange)',
    '0 0 4px var(--cyber-glow-orange)',
  ],
  gold: [
    '0 0 4px var(--cyber-glow-gold)',
    '0 0 12px var(--cyber-glow-gold)',
    '0 0 4px var(--cyber-glow-gold)',
  ],
  green: [
    '0 0 4px oklch(0.792 0.209 151.711 / 0.4)',
    '0 0 12px oklch(0.792 0.209 151.711 / 0.4)',
    '0 0 4px oklch(0.792 0.209 151.711 / 0.4)',
  ],
  red: [
    '0 0 4px oklch(0.637 0.237 25.331 / 0.4)',
    '0 0 12px oklch(0.637 0.237 25.331 / 0.4)',
    '0 0 4px oklch(0.637 0.237 25.331 / 0.4)',
  ],
};

export function NeonBadge({
  children,
  variant = 'pink',
  glow = false,
  className,
}: NeonBadgeProps) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.92 }}
      animate={
        glow
          ? {
              opacity: 1,
              scale: 1,
              boxShadow: glowAnimation[variant],
            }
          : { opacity: 1, scale: 1 }
      }
      transition={
        glow
          ? {
              opacity: { duration: 0.2 },
              scale: { duration: 0.2 },
              boxShadow: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
            }
          : { duration: 0.2 }
      }
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold font-mono tracking-wide',
        'bg-cyber-surface/50',
        variantStyles[variant],
        glow && glowStyles[variant],
        className,
      )}
    >
      {children}
    </motion.span>
  );
}
