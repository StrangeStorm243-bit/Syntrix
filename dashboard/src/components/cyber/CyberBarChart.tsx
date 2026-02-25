import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import {
  TOOLTIP_STYLE, AXIS_STROKE, AXIS_FONT_SIZE, FUNNEL_COLORS, GRADIENT_IDS,
  NeonGradientDefs,
} from '../../lib/chart-theme';
import { cn } from '../../lib/utils';

interface CyberBarChartProps {
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  dataKey: string;
  xAxisKey: string;
  height?: number;
  fillMode?: 'gradient' | 'cells';
  gradientId?: string;
  colors?: string[];
  tickFormatter?: (value: unknown) => string;
  emptyMessage?: string;
  className?: string;
}

export function CyberBarChart({
  title,
  data,
  dataKey,
  xAxisKey,
  height = 250,
  fillMode = 'gradient',
  gradientId = GRADIENT_IDS.pinkOrange,
  colors = FUNNEL_COLORS,
  tickFormatter,
  emptyMessage = 'No data yet',
  className,
}: CyberBarChartProps) {
  return (
    <div className={cn('glass rounded-lg p-4', className)}>
      <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">{title}</h2>
      {data.length === 0 ? (
        <p className="py-10 text-center text-sm text-cyber-text-dim">{emptyMessage}</p>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data}>
            <defs>
              <NeonGradientDefs />
            </defs>
            <XAxis
              dataKey={xAxisKey}
              stroke={AXIS_STROKE}
              fontSize={AXIS_FONT_SIZE}
              tickFormatter={tickFormatter}
            />
            <YAxis stroke={AXIS_STROKE} fontSize={AXIS_FONT_SIZE} />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              labelStyle={{ color: TOOLTIP_STYLE.color }}
            />
            <Bar
              dataKey={dataKey}
              radius={[4, 4, 0, 0]}
              fill={fillMode === 'gradient' ? `url(#${gradientId})` : colors[0]}
            >
              {fillMode === 'cells' &&
                data.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
