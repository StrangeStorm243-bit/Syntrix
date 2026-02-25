/**
 * Shared neon chart theme for all Recharts components.
 * Provides gradient definitions, tooltip styles, and axis config.
 */

/** Neon gradient ID references — use in <defs> SVG blocks */
export const GRADIENT_IDS = {
  pinkOrange: 'neonPinkOrange',
  orangeGold: 'neonOrangeGold',
  pink: 'neonPink',
  gold: 'neonGold',
} as const;

/** Neon colors as CSS strings for Recharts props that don't support gradients */
export const NEON_COLORS = {
  pink: 'oklch(0.655 0.261 356.9)',
  orange: 'oklch(0.705 0.193 39.2)',
  gold: 'oklch(0.887 0.182 95.3)',
  pinkDim: 'oklch(0.400 0.160 356.9)',
  orangeDim: 'oklch(0.450 0.120 39.2)',
  textDim: 'oklch(0.600 0.010 95.3)',
  text: 'oklch(0.920 0.010 95.3)',
} as const;

/** Glassmorphism tooltip style for Recharts <Tooltip contentStyle={...}> */
export const TOOLTIP_STYLE: React.CSSProperties = {
  background: 'oklch(0.130 0.010 345.1 / 0.85)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid oklch(0.655 0.261 356.9 / 0.25)',
  borderRadius: 8,
  boxShadow: '0 0 15px oklch(0.655 0.261 356.9 / 0.1)',
  color: 'oklch(0.920 0.010 95.3)',
};

/** Axis stroke color */
export const AXIS_STROKE = 'oklch(0.600 0.010 95.3)';
export const AXIS_FONT_SIZE = 12;

/** Funnel chart color sequence */
export const FUNNEL_COLORS = [
  'oklch(0.655 0.261 356.9)',  // pink
  'oklch(0.680 0.230 18)',     // pink-orange blend
  'oklch(0.705 0.193 39.2)',   // orange
  'oklch(0.800 0.188 67)',     // orange-gold blend
  'oklch(0.887 0.182 95.3)',   // gold
];

/**
 * Shared SVG gradient definitions for all neon charts.
 * Drop inside `<defs><NeonGradientDefs /></defs>` in any Recharts chart.
 */
export function NeonGradientDefs() {
  return (
    <>
      <linearGradient id={GRADIENT_IDS.pinkOrange} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={NEON_COLORS.pink} stopOpacity={1} />
        <stop offset="100%" stopColor={NEON_COLORS.orange} stopOpacity={0.8} />
      </linearGradient>
      <linearGradient id={GRADIENT_IDS.orangeGold} x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor={NEON_COLORS.pink} stopOpacity={1} />
        <stop offset="100%" stopColor={NEON_COLORS.orange} stopOpacity={0.9} />
      </linearGradient>
      <linearGradient id={GRADIENT_IDS.pink} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={NEON_COLORS.pink} stopOpacity={1} />
        <stop offset="100%" stopColor={NEON_COLORS.pinkDim} stopOpacity={0.7} />
      </linearGradient>
      <linearGradient id={GRADIENT_IDS.gold} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={NEON_COLORS.gold} stopOpacity={1} />
        <stop offset="100%" stopColor={NEON_COLORS.orangeDim} stopOpacity={0.7} />
      </linearGradient>
    </>
  );
}
