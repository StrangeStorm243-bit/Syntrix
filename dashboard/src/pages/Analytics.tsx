import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  FunnelChart, Funnel, LabelList,
} from 'recharts';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { NeonTable, type NeonColumn } from '../components/cyber/NeonTable';
import { useScoreDistribution, useConversionFunnel, useQueryPerformance } from '../hooks/useAnalytics';
import {
  TOOLTIP_STYLE, AXIS_STROKE, AXIS_FONT_SIZE, NEON_COLORS, FUNNEL_COLORS,
} from '../lib/chart-theme';

interface QueryPerf {
  query_label: string;
  total_leads: number;
  avg_score: number;
  relevant_pct: number;
}

const queryColumns: NeonColumn<QueryPerf>[] = [
  { key: 'query_label', header: 'Query' },
  { key: 'total_leads', header: 'Leads', className: 'font-mono' },
  {
    key: 'avg_score',
    header: 'Avg Score',
    className: 'font-mono',
    render: (row) => (
      <span className="text-cyber-gold">{row.avg_score}</span>
    ),
  },
  {
    key: 'relevant_pct',
    header: 'Relevant %',
    className: 'font-mono',
    render: (row) => (
      <span className="text-cyber-orange">{row.relevant_pct}%</span>
    ),
  },
];

export default function Analytics() {
  const { data: scores, isLoading: scoresLoading } = useScoreDistribution();
  const { data: funnel } = useConversionFunnel();
  const { data: queryPerf } = useQueryPerformance();

  if (scoresLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-cyber-text">Analytics</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Score Distribution — neon pink→orange gradient bars */}
        <div className="glass rounded-lg p-4">
          <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">Score Distribution</h2>
          {scores && scores.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={scores}>
                <defs>
                  <linearGradient id="scoreGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor={NEON_COLORS.pink} stopOpacity={1} />
                    <stop offset="100%" stopColor={NEON_COLORS.orange} stopOpacity={0.9} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="bucket_min"
                  stroke={AXIS_STROKE}
                  fontSize={AXIS_FONT_SIZE}
                  tickFormatter={(v: number) => `${v}-${v + 10}`}
                />
                <YAxis stroke={AXIS_STROKE} fontSize={AXIS_FONT_SIZE} />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  labelStyle={{ color: TOOLTIP_STYLE.color }}
                />
                <Bar dataKey="count" fill="url(#scoreGradient)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-10 text-center text-sm text-cyber-text-dim">No score data yet</p>
          )}
        </div>

        {/* Conversion Funnel — neon color sequence */}
        <div className="glass rounded-lg p-4">
          <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">Conversion Funnel</h2>
          {funnel && funnel.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <FunnelChart>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Funnel dataKey="count" data={funnel} isAnimationActive>
                  <LabelList
                    position="right"
                    fill={NEON_COLORS.text}
                    stroke="none"
                    dataKey="stage"
                    fontSize={12}
                  />
                  {funnel.map((_entry, index) => (
                    <Cell
                      key={`funnel-${index}`}
                      fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]}
                    />
                  ))}
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-10 text-center text-sm text-cyber-text-dim">No funnel data yet</p>
          )}
        </div>

        {/* Query Performance — NeonTable with glow highlights */}
        <div className="col-span-full glass rounded-lg p-4">
          <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">Query Performance</h2>
          <NeonTable
            columns={queryColumns}
            data={queryPerf ?? []}
            keyField="query_label"
            emptyMessage="No query data yet"
          />
        </div>
      </div>
    </div>
  );
}
