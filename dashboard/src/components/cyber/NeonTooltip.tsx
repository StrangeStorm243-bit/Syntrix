import { useState, useRef, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils';

type TooltipSide = 'top' | 'bottom' | 'left' | 'right';

interface NeonTooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: TooltipSide;
}

const sidePositions: Record<TooltipSide, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

export function NeonTooltip({ content, children, side = 'top' }: NeonTooltipProps) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<number | null>(null);

  const show = useCallback(() => {
    timerRef.current = window.setTimeout(() => setVisible(true), 200);
  }, []);

  const hide = useCallback(() => {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    setVisible(false);
  }, []);

  return (
    <div className="relative inline-flex" onMouseEnter={show} onMouseLeave={hide}>
      {children}
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'glass-strong absolute z-50 rounded px-3 py-1.5 text-xs text-cyber-text whitespace-nowrap',
              'border border-cyber-pink/30 pointer-events-none',
              sidePositions[side],
            )}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
