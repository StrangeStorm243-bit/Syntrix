import { motion } from 'motion/react';
import { scaleIn } from '../../lib/animation-presets';
import { cn } from '../../lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  augmented?: boolean;
}

export function GlassCard({ children, className, augmented }: GlassCardProps) {
  return (
    <motion.div
      variants={scaleIn}
      initial="hidden"
      animate="visible"
      className={cn('glass glass-hover rounded-lg p-4', className)}
      {...(augmented
        ? { 'data-augmented-ui': 'tl-clip br-clip border' }
        : {})}
    >
      {children}
    </motion.div>
  );
}
