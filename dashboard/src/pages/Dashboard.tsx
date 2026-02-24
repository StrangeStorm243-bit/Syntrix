import { Users, MessageSquare, Send, Target } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { MetricCard } from '../components/MetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useStats } from '../hooks/useStats';
import { useConversionFunnel } from '../hooks/useAnalytics';

export default function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const { data: funnel } = useConversionFunnel();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Total Leads" value={stats?.scored ?? 0} icon={<Users size={18} />} />
        <MetricCard label="Pending Drafts" value={stats?.drafted ?? 0} icon={<MessageSquare size={18} />} />
        <MetricCard label="Sent" value={stats?.sent ?? 0} icon={<Send size={18} />} />
        <MetricCard label="Outcomes" value={stats?.outcomes ?? 0} icon={<Target size={18} />} />
      </div>

      {/* Funnel chart */}
      {funnel && funnel.length > 0 && (
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
          <h2 className="mb-4 text-sm font-medium text-gray-400">Pipeline Funnel</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={funnel}>
              <XAxis dataKey="stage" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#e5e7eb' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
