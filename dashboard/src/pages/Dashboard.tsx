import { Users, MessageSquare, Send, Target } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { NeonMetricCard } from '../components/cyber/NeonMetricCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useStats } from '../hooks/useStats';
import { useConversionFunnel } from '../hooks/useAnalytics';
import { useGPUTier } from '../hooks/useGPUTier';
import { lazy3D, Suspense3D } from '../lib/lazy-3d';
import {
  TOOLTIP_STYLE, AXIS_STROKE, AXIS_FONT_SIZE, FUNNEL_COLORS,
} from '../lib/chart-theme';

const HeroScene = lazy3D(() => import('../scenes/HeroScene'));

export default function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const { data: funnel } = useConversionFunnel();
  const { tier: gpuTier } = useGPUTier();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  return (
    <div className="relative space-y-6">
      <Suspense3D>
        <HeroScene gpuTier={gpuTier} />
      </Suspense3D>
      <h1 className="text-2xl font-bold text-cyber-text">Dashboard</h1>

      {/* Metric cards — animated counters with neon glow */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <NeonMetricCard title="Total Leads" value={stats?.scored ?? 0} icon={<Users size={18} />} />
        <NeonMetricCard title="Pending Drafts" value={stats?.drafted ?? 0} icon={<MessageSquare size={18} />} />
        <NeonMetricCard title="Sent" value={stats?.sent ?? 0} icon={<Send size={18} />} />
        <NeonMetricCard title="Outcomes" value={stats?.outcomes ?? 0} icon={<Target size={18} />} />
      </div>

      {/* Conversion funnel chart — neon gradients + glass tooltip */}
      {funnel && funnel.length > 0 && (
        <div className="glass rounded-lg p-4">
          <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">Pipeline Funnel</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={funnel}>
              <defs>
                <linearGradient id="neonBarGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.655 0.261 356.9)" stopOpacity={1} />
                  <stop offset="100%" stopColor="oklch(0.705 0.193 39.2)" stopOpacity={0.8} />
                </linearGradient>
              </defs>
              <XAxis dataKey="stage" stroke={AXIS_STROKE} fontSize={AXIS_FONT_SIZE} />
              <YAxis stroke={AXIS_STROKE} fontSize={AXIS_FONT_SIZE} />
              <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={{ color: TOOLTIP_STYLE.color }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {funnel.map((_entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
