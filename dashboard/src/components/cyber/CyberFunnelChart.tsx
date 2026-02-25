import {
  FunnelChart as RechartsFunnelChart,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { TOOLTIP_STYLE, NEON_COLORS, FUNNEL_COLORS } from '../../lib/chart-theme';
import { cn } from '../../lib/utils';

interface CyberFunnelChartProps {
  title: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  dataKey: string;
  labelKey: string;
  height?: number;
  colors?: string[];
  emptyMessage?: string;
  className?: string;
}

export function CyberFunnelChart({
  title,
  data,
  dataKey,
  labelKey,
  height = 250,
  colors = FUNNEL_COLORS,
  emptyMessage = 'No data yet',
  className,
}: CyberFunnelChartProps) {
  return (
    <div className={cn('glass rounded-lg p-4', className)}>
      <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">{title}</h2>
      {data.length === 0 ? (
        <p className="py-10 text-center text-sm text-cyber-text-dim">{emptyMessage}</p>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <RechartsFunnelChart>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Funnel dataKey={dataKey} data={data} isAnimationActive>
              <LabelList
                position="right"
                fill={NEON_COLORS.text}
                stroke="none"
                dataKey={labelKey}
                fontSize={12}
              />
              {data.map((_entry, index) => (
                <Cell key={`funnel-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Funnel>
          </RechartsFunnelChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
