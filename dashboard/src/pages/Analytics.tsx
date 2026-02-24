import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  FunnelChart, Funnel, LabelList,
} from 'recharts';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useScoreDistribution, useConversionFunnel, useQueryPerformance } from '../hooks/useAnalytics';

export default function Analytics() {
  const { data: scores, isLoading: scoresLoading } = useScoreDistribution();
  const { data: funnel } = useConversionFunnel();
  const { data: queryPerf } = useQueryPerformance();

  if (scoresLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  const chartStyle = { background: '#1f2937', border: '1px solid #374151', borderRadius: 8 };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Score Distribution */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <h2 className="mb-4 text-sm font-medium text-gray-400">Score Distribution</h2>
          {scores && scores.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={scores}>
                <XAxis
                  dataKey="bucket_min"
                  stroke="#9ca3af"
                  fontSize={12}
                  tickFormatter={(v: number) => `${v}-${v + 10}`}
                />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip contentStyle={chartStyle} labelStyle={{ color: '#e5e7eb' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-10 text-center text-sm text-gray-500">No score data yet</p>
          )}
        </div>

        {/* Conversion Funnel */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <h2 className="mb-4 text-sm font-medium text-gray-400">Conversion Funnel</h2>
          {funnel && funnel.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <FunnelChart>
                <Tooltip contentStyle={chartStyle} />
                <Funnel dataKey="count" data={funnel} isAnimationActive>
                  <LabelList position="right" fill="#e5e7eb" stroke="none" dataKey="stage" fontSize={12} />
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-10 text-center text-sm text-gray-500">No funnel data yet</p>
          )}
        </div>

        {/* Query Performance */}
        <div className="col-span-full rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <h2 className="mb-4 text-sm font-medium text-gray-400">Query Performance</h2>
          {queryPerf && queryPerf.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-gray-400">
                  <tr>
                    <th className="px-4 py-2">Query</th>
                    <th className="px-4 py-2">Leads</th>
                    <th className="px-4 py-2">Avg Score</th>
                    <th className="px-4 py-2">Relevant %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {queryPerf.map((q) => (
                    <tr key={q.query_label}>
                      <td className="px-4 py-2 text-white">{q.query_label}</td>
                      <td className="px-4 py-2">{q.total_leads}</td>
                      <td className="px-4 py-2">{q.avg_score}</td>
                      <td className="px-4 py-2">{q.relevant_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="py-10 text-center text-sm text-gray-500">No query data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
