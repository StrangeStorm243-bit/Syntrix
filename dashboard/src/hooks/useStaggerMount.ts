import type { Variants } from 'motion/react';
import { useReducedMotion } from './useReducedMotion';

export function useStaggerMount(): {
  containerVariants: Variants;
  itemVariants: Variants;
  isReducedMotion: boolean;
} {
  const isReducedMotion = useReducedMotion();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: isReducedMotion ? 0 : 0.08,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: isReducedMotion ? { opacity: 1 } : { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, ease: 'easeOut' },
    },
  };

  return { containerVariants, itemVariants, isReducedMotion };
}
