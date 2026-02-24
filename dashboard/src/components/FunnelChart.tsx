import {
  FunnelChart as RechartsFunnel,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface FunnelStep {
  stage: string;
  count: number;
}

interface FunnelChartProps {
  data: FunnelStep[];
  height?: number;
}

const CHART_TOOLTIP_STYLE = {
  background: '#1f2937',
  border: '1px solid #374151',
  borderRadius: 8,
};

export function FunnelChart({ data, height = 250 }: FunnelChartProps) {
  if (!data || data.length === 0) {
    return <p className="py-10 text-center text-sm text-gray-500">No funnel data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsFunnel>
        <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
        <Funnel dataKey="count" data={data} isAnimationActive>
          <LabelList
            position="right"
            fill="#e5e7eb"
            stroke="none"
            dataKey="stage"
            fontSize={12}
          />
        </Funnel>
      </RechartsFunnel>
    </ResponsiveContainer>
  );
}
