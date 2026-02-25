import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface NeonInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

/**
 * Cyberpunk-styled text input with glass background, neon pink focus glow,
 * monospace value font, error state glow, and optional label.
 */
export const NeonInput = forwardRef<HTMLInputElement, NeonInputProps>(
  function NeonInput({ label, error, className, id, ...rest }, ref) {
    // Generate a stable id for label<->input association when none is provided.
    const inputId = id ?? (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm text-cyber-text-dim"
          >
            {label}
          </label>
        )}

        <input
          ref={ref}
          id={inputId}
          className={cn(
            // Base layout + typography
            'w-full rounded px-3 py-2 text-sm font-mono text-cyber-text',
            // Glass background
            'glass',
            // Default border
            'border border-cyber-pink/20 outline-none',
            // Placeholder colour
            'placeholder:text-cyber-text-dim/50',
            // Normal focus — pink neon glow
            'focus:border-cyber-pink/60',
            'focus:shadow-[0_0_0_1px_rgba(255,20,147,0.4),0_0_12px_rgba(255,20,147,0.25)]',
            // Transition for smooth glow appearance
            'transition-shadow duration-200',
            // Error overrides
            error && [
              'border-red-500/60',
              'focus:border-red-500/80',
              'focus:shadow-[0_0_0_1px_rgba(239,68,68,0.4),0_0_12px_rgba(239,68,68,0.25)]',
            ],
            className,
          )}
          {...rest}
        />

        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
      </div>
    );
  },
);
