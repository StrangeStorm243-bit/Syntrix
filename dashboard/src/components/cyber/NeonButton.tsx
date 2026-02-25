import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

type NeonButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type NeonButtonSize = 'sm' | 'md' | 'lg';

interface NeonButtonProps {
  children: React.ReactNode;
  variant?: NeonButtonVariant;
  size?: NeonButtonSize;
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit';
}

const variantBase: Record<NeonButtonVariant, string> = {
  primary: 'border-cyber-pink text-cyber-pink hover:shadow-[0_0_12px_var(--cyber-glow-pink)] hover:bg-cyber-pink/10',
  secondary: 'border-cyber-orange text-cyber-orange hover:shadow-[0_0_12px_var(--cyber-glow-orange)] hover:bg-cyber-orange/10',
  danger: 'border-red-500 text-red-400 hover:shadow-[0_0_12px_oklch(0.637_0.237_25.331_/_0.4)] hover:bg-red-500/10',
  ghost: 'border-transparent text-cyber-text-dim hover:border-cyber-pink/30 hover:text-cyber-text hover:bg-cyber-surface-bright/50',
};

const sizeStyles: Record<NeonButtonSize, string> = {
  sm: 'px-3 py-1 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

const disabledVariant: Record<NeonButtonVariant, string> = {
  primary: 'border-cyber-pink-dim text-cyber-pink-dim',
  secondary: 'border-cyber-orange-dim text-cyber-orange-dim',
  danger: 'border-red-800 text-red-700',
  ghost: 'border-transparent text-cyber-text-dim/50',
};

export function NeonButton({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className,
  type = 'button',
}: NeonButtonProps) {
  return (
    <motion.button
      type={type}
      onClick={disabled ? undefined : onClick}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      whileHover={disabled ? undefined : { scale: 1.02 }}
      transition={{ duration: 0.15 }}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded border font-mono font-semibold tracking-wide',
        'bg-cyber-surface/50 backdrop-blur-sm',
        'transition-shadow transition-colors duration-200',
        'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyber-pink',
        sizeStyles[size],
        disabled
          ? cn(disabledVariant[variant], 'opacity-40 cursor-not-allowed shadow-none')
          : variantBase[variant],
        className,
      )}
    >
      {children}
    </motion.button>
  );
}
