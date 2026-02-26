import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Workflow,
  ChevronDown,
  ChevronUp,
  Play,
  Pause,
  Users,
  CheckCircle2,
  Heart,
  MessageSquare,
  UserPlus,
  Send,
  Eye,
} from 'lucide-react';
import { GlassCard } from '../components/cyber/GlassCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useSequences, useEnrollments } from '../hooks/useSequences';
import { useStaggerMount } from '../hooks/useStaggerMount';
import type { Sequence } from '../hooks/useSequences';

const ACTION_ICONS: Record<string, typeof Heart> = {
  like: Heart,
  reply: MessageSquare,
  follow: UserPlus,
  dm: Send,
  view_profile: Eye,
};

function getActionIcon(actionType: string) {
  return ACTION_ICONS[actionType] || Play;
}

function StepVisualization({ steps }: { steps: Sequence['steps'] }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto py-2">
      {steps.map((step, i) => {
        const Icon = getActionIcon(step.action_type);
        return (
          <div key={step.order} className="flex items-center gap-1 shrink-0">
            <div className="flex flex-col items-center gap-1">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-full border border-cyber-pink/30 bg-cyber-pink/10"
                title={step.action_type}
              >
                <Icon size={14} className="text-cyber-pink" />
              </div>
              <span className="text-[10px] font-mono text-cyber-text-dim whitespace-nowrap">
                {step.action_type.replace('_', ' ')}
              </span>
              {step.delay_hours > 0 && (
                <span className="text-[9px] font-mono text-cyber-text-dim/60">
                  +{step.delay_hours}h
                </span>
              )}
            </div>
            {i < steps.length - 1 && (
              <div className="flex items-center self-start mt-4">
                <div className="h-px w-4 bg-cyber-pink/30" />
                <div className="h-0 w-0 border-t-[3px] border-b-[3px] border-l-[4px] border-transparent border-l-cyber-pink/30" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function EnrollmentList({ sequenceId }: { sequenceId: number }) {
  const { data, isLoading } = useEnrollments(sequenceId);

  if (isLoading) return <LoadingSpinner className="mx-auto my-4" />;

  const enrollments = data?.items ?? [];
  if (enrollments.length === 0) {
    return (
      <p className="py-4 text-center text-xs text-cyber-text-dim">
        No leads enrolled in this sequence yet.
      </p>
    );
  }

  return (
    <div className="mt-3 space-y-1">
      {enrollments.map((enrollment) => (
        <div
          key={enrollment.id}
          className="flex items-center justify-between rounded-md border border-white/5 bg-cyber-surface/30 px-3 py-2"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-mono text-cyber-text">
              @{enrollment.author_username || 'unknown'}
            </span>
            <StatusBadge status={enrollment.status} />
          </div>
          <div className="flex items-center gap-3 text-xs text-cyber-text-dim">
            <span className="font-mono">
              Step {enrollment.current_step + 1}
            </span>
            <span>
              {new Date(enrollment.started_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    active: 'border-green-500/30 bg-green-500/10 text-green-400',
    completed: 'border-cyber-pink/30 bg-cyber-pink/10 text-cyber-pink',
    paused: 'border-cyber-orange/30 bg-cyber-orange/10 text-cyber-orange',
    failed: 'border-red-500/30 bg-red-500/10 text-red-400',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-mono border ${
        colorMap[status] || 'border-cyber-surface-bright text-cyber-text-dim'
      }`}
    >
      {status}
    </span>
  );
}

function SequenceCard({ sequence }: { sequence: Sequence }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <GlassCard className="overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-cyber-text">{sequence.name}</h3>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-mono border ${
                sequence.is_active
                  ? 'border-green-500/30 bg-green-500/10 text-green-400'
                  : 'border-cyber-surface-bright bg-cyber-surface/30 text-cyber-text-dim'
              }`}
            >
              {sequence.is_active ? (
                <>
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400 shadow-[0_0_4px_rgba(34,197,94,0.5)]" />
                  Active
                </>
              ) : (
                <>
                  <Pause size={8} />
                  Paused
                </>
              )}
            </span>
          </div>
          <p className="mt-1 text-xs text-cyber-text-dim">{sequence.description}</p>
        </div>
      </div>

      {/* Step visualization */}
      <StepVisualization steps={sequence.steps} />

      {/* Stats row */}
      <div className="flex items-center gap-4 border-t border-white/5 pt-3">
        <div className="flex items-center gap-1.5">
          <Users size={12} className="text-cyber-pink" />
          <span className="text-xs font-mono text-cyber-text">
            {sequence.enrolled_count}
          </span>
          <span className="text-[10px] text-cyber-text-dim">enrolled</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Play size={12} className="text-green-400" />
          <span className="text-xs font-mono text-cyber-text">
            {sequence.active_count}
          </span>
          <span className="text-[10px] text-cyber-text-dim">active</span>
        </div>
        <div className="flex items-center gap-1.5">
          <CheckCircle2 size={12} className="text-cyber-gold" />
          <span className="text-xs font-mono text-cyber-text">
            {sequence.completed_count}
          </span>
          <span className="text-[10px] text-cyber-text-dim">completed</span>
        </div>
      </div>

      {/* Expandable enrollments section */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="mt-2 flex w-full items-center justify-center gap-1 rounded-md border border-white/5 py-1.5 text-xs font-mono text-cyber-text-dim hover:border-cyber-pink/20 hover:text-cyber-text transition-colors"
      >
        {expanded ? (
          <>
            Hide Enrollments <ChevronUp size={12} />
          </>
        ) : (
          <>
            Show Enrollments ({sequence.enrolled_count}) <ChevronDown size={12} />
          </>
        )}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <EnrollmentList sequenceId={sequence.id} />
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  );
}

export default function Sequences() {
  const { data, isLoading } = useSequences();
  const { containerVariants, itemVariants } = useStaggerMount();

  if (isLoading) return <LoadingSpinner className="mx-auto mt-20" />;

  const sequences = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Workflow size={22} className="text-cyber-pink" />
          <h1 className="text-2xl font-bold text-cyber-text">Sequences</h1>
        </div>
        <span className="text-sm text-cyber-text-dim">
          {data?.total ?? 0} sequence{(data?.total ?? 0) !== 1 ? 's' : ''}
        </span>
      </div>

      {sequences.length === 0 ? (
        <EmptyState
          title="No sequences yet"
          description="Sequences will appear here once you complete setup and the pipeline creates them."
        />
      ) : (
        <motion.div
          className="grid gap-4 lg:grid-cols-2"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {sequences.map((seq) => (
            <motion.div key={seq.id} variants={itemVariants}>
              <SequenceCard sequence={seq} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
