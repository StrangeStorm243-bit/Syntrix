import { Users, MessageSquare, Send, Target } from 'lucide-react';
import { motion } from 'motion/react';
import { NeonMetricCard } from '../components/cyber/NeonMetricCard';
import { CyberBarChart } from '../components/cyber/CyberBarChart';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useStats } from '../hooks/useStats';
import { useConversionFunnel } from '../hooks/useAnalytics';
import { useGPUTier } from '../hooks/useGPUTier';
import { useStaggerMount } from '../hooks/useStaggerMount';
import { usePerformanceMode } from '../hooks/usePerformanceMode';
import { lazy3D, Suspense3D } from '../lib/lazy-3d';
import { FUNNEL_COLORS } from '../lib/chart-theme';

const HeroScene = lazy3D(() => import('../scenes/HeroScene'));

export default function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const { data: funnel } = useConversionFunnel();
  const { tier: gpuTier } = useGPUTier();
  const { containerVariants, itemVariants } = useStaggerMount();
  const { performanceMode } = usePerformanceMode();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  return (
    <div className="relative space-y-6">
      {!performanceMode && (
        <Suspense3D>
          <HeroScene gpuTier={gpuTier} />
        </Suspense3D>
      )}
      <h1 className="text-2xl font-bold text-cyber-text">Dashboard</h1>

      {/* Metric cards — stagger-animated on mount */}
      <motion.div
        className="grid grid-cols-2 gap-4 lg:grid-cols-4"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div variants={itemVariants}>
          <NeonMetricCard title="Total Leads" value={stats?.scored ?? 0} icon={<Users size={18} />} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <NeonMetricCard title="Pending Drafts" value={stats?.drafted ?? 0} icon={<MessageSquare size={18} />} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <NeonMetricCard title="Sent" value={stats?.sent ?? 0} icon={<Send size={18} />} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <NeonMetricCard title="Outcomes" value={stats?.outcomes ?? 0} icon={<Target size={18} />} />
        </motion.div>
      </motion.div>

      {/* Conversion funnel chart — neon cell colors */}
      {funnel && funnel.length > 0 && (
        <motion.div variants={itemVariants} initial="hidden" animate="visible">
          <CyberBarChart
            title="Pipeline Funnel"
            data={funnel}
            dataKey="count"
            xAxisKey="stage"
            fillMode="cells"
            colors={FUNNEL_COLORS}
          />
        </motion.div>
      )}
    </div>
  );
}
