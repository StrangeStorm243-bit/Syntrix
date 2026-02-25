import { LoadingSpinner } from '../components/LoadingSpinner';
import { NeonTable, type NeonColumn } from '../components/cyber/NeonTable';
import { CyberBarChart } from '../components/cyber/CyberBarChart';
import { CyberFunnelChart } from '../components/cyber/CyberFunnelChart';
import { useScoreDistribution, useConversionFunnel, useQueryPerformance } from '../hooks/useAnalytics';
import { GRADIENT_IDS } from '../lib/chart-theme';

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
        <CyberBarChart
          title="Score Distribution"
          data={scores ?? []}
          dataKey="count"
          xAxisKey="bucket_min"
          fillMode="gradient"
          gradientId={GRADIENT_IDS.orangeGold}
          tickFormatter={(v: unknown) => `${v}-${Number(v) + 10}`}
          emptyMessage="No score data yet"
        />

        {/* Conversion Funnel — neon color sequence */}
        <CyberFunnelChart
          title="Conversion Funnel"
          data={funnel ?? []}
          dataKey="count"
          labelKey="stage"
          emptyMessage="No funnel data yet"
        />

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
