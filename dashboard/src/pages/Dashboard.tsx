import { Users, MessageSquare, Send, Target, Workflow, UserCheck } from 'lucide-react';
import { motion } from 'motion/react';
import { NeonMetricCard } from '../components/cyber/NeonMetricCard';
import { CyberBarChart } from '../components/cyber/CyberBarChart';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useStats } from '../hooks/useStats';
import { useSequences } from '../hooks/useSequences';
import { useConversionFunnel } from '../hooks/useAnalytics';
import { useGPUTier } from '../hooks/useGPUTier';
import { useStaggerMount } from '../hooks/useStaggerMount';
import { usePerformanceMode } from '../hooks/usePerformanceMode';
import { lazy3D, Suspense3D } from '../lib/lazy-3d';
import { FUNNEL_COLORS } from '../lib/chart-theme';
import { FlipCard } from '../components/cyber/FlipCard';

const HeroScene = lazy3D(() => import('../scenes/HeroScene'));

export default function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const { data: funnel } = useConversionFunnel();
  const { data: sequences } = useSequences();
  const { tier: gpuTier } = useGPUTier();
  const { containerVariants, itemVariants } = useStaggerMount();
  const { performanceMode } = usePerformanceMode();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  // Compute sequence metrics
  const activeSequences = sequences?.items.filter((s) => s.is_active).length ?? 0;
  const enrolledLeads = sequences?.items.reduce((sum, s) => sum + s.enrolled_count, 0) ?? 0;

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
        className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6"
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
        <motion.div variants={itemVariants}>
          <NeonMetricCard
            title="Active Sequences"
            value={activeSequences}
            icon={<Workflow size={18} />}
            color="orange"
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <NeonMetricCard
            title="Enrolled Leads"
            value={enrolledLeads}
            icon={<UserCheck size={18} />}
            color="gold"
          />
        </motion.div>
      </motion.div>

      {/* Conversion funnel + decorative art */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
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
        <motion.div variants={itemVariants} initial="hidden" animate="visible">
          <FlipCard
            frontSrc="/images/signal-front.png"
            backSrc="/images/signal-back.png"
            alt="Signal in the Noise"
            className="h-64 w-full"
            autoFlipInterval={6000}
          />
        </motion.div>
      </div>
    </div>
  );
}
