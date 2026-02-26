import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  MessageSquare,
  Send,
  Target,
  Workflow,
  UserCheck,
  Rocket,
  Info,
  Play,
  X,
} from 'lucide-react';
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
  const [bannerDismissed, setBannerDismissed] = useState(() => {
    return localStorage.getItem('syntrix-welcome-dismissed') === 'true';
  });

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  // Compute sequence metrics
  const activeSequences = sequences?.items.filter((s) => s.is_active).length ?? 0;
  const enrolledLeads = sequences?.items.reduce((sum, s) => sum + s.enrolled_count, 0) ?? 0;

  // Show welcome banner when pipeline hasn't been run yet
  const isNewUser =
    !bannerDismissed &&
    (stats?.collected ?? 0) === 0 &&
    (stats?.sent ?? 0) === 0;

  function dismissBanner() {
    setBannerDismissed(true);
    localStorage.setItem('syntrix-welcome-dismissed', 'true');
  }

  return (
    <div className="relative space-y-6">
      {!performanceMode && (
        <Suspense3D>
          <HeroScene gpuTier={gpuTier} />
        </Suspense3D>
      )}
      <h1 className="text-2xl font-bold text-cyber-text">Dashboard</h1>

      {/* Welcome banner for new users */}
      {isNewUser && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="relative overflow-hidden rounded-lg p-5"
          style={{
            background:
              'linear-gradient(135deg, rgba(255,20,147,0.12) 0%, rgba(255,107,53,0.08) 50%, rgba(6,182,212,0.08) 100%)',
            border: '1px solid rgba(255,20,147,0.25)',
            boxShadow: '0 0 30px rgba(255,20,147,0.08)',
          }}
        >
          <button
            type="button"
            onClick={dismissBanner}
            className="absolute right-3 top-3 rounded-md p-1 text-cyber-text-dim hover:text-cyber-text transition-colors"
          >
            <X size={14} />
          </button>
          <div className="flex items-start gap-4">
            <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
              style={{
                background: 'rgba(255,20,147,0.15)',
                border: '1px solid rgba(255,20,147,0.3)',
              }}
            >
              <Rocket size={20} className="text-cyber-pink" />
            </div>
            <div className="flex-1">
              <h2 className="text-sm font-semibold text-cyber-text">
                Welcome to Syntrix!
              </h2>
              <p className="mt-1 text-xs text-cyber-text-dim leading-relaxed">
                Your pipeline is set up and ready to go. Follow these steps to start finding leads:
              </p>
              <div className="mt-3 space-y-2">
                <Link
                  to="/how-it-works"
                  className="group flex items-center gap-3 rounded-md px-3 py-2.5 text-xs font-medium transition-all duration-200"
                  style={{
                    background: 'rgba(255,20,147,0.08)',
                    border: '1px solid rgba(255,20,147,0.2)',
                  }}
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-cyber-pink/20 text-[10px] font-bold text-cyber-pink">1</span>
                  <Play size={14} className="text-cyber-pink group-hover:text-pink-300" />
                  <span className="text-cyber-text-dim group-hover:text-cyber-text">
                    Run your first pipeline — collect tweets, judge relevance, score leads, and draft replies
                  </span>
                </Link>
                <Link
                  to="/queue"
                  className="group flex items-center gap-3 rounded-md px-3 py-2.5 text-xs font-medium transition-all duration-200"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/10 text-[10px] font-bold text-cyber-text-dim">2</span>
                  <Send size={14} className="text-cyan-400 group-hover:text-cyan-300" />
                  <span className="text-cyber-text-dim group-hover:text-cyber-text">
                    Review the queue — approve, edit, or reject AI-drafted replies before sending
                  </span>
                </Link>
                <Link
                  to="/analytics"
                  className="group flex items-center gap-3 rounded-md px-3 py-2.5 text-xs font-medium transition-all duration-200"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/10 text-[10px] font-bold text-cyber-text-dim">3</span>
                  <Target size={14} className="text-green-400 group-hover:text-green-300" />
                  <span className="text-cyber-text-dim group-hover:text-cyber-text">
                    Track results — monitor conversions, engagement rates, and pipeline performance
                  </span>
                </Link>
              </div>
            </div>
          </div>
        </motion.div>
      )}

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
