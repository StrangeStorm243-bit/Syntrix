import type { Variants } from 'motion/react';

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.4 } },
};

export const slideUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3 } },
};

export const glowPulse: Variants = {
  idle: { boxShadow: '0 0 5px rgba(255,20,147,0.2)' },
  active: {
    boxShadow: [
      '0 0 5px rgba(255,20,147,0.2)',
      '0 0 15px rgba(255,20,147,0.4)',
      '0 0 5px rgba(255,20,147,0.2)',
    ],
    transition: { duration: 2, repeat: Infinity },
  },
};
