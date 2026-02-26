import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { usePipelineFlow } from '../hooks/usePipelineFlow';
import { PipelineDAG } from '../pipeline/PipelineDAG';
import { ActivityFeed } from '../pipeline/ActivityFeed';
import { usePerformanceMode } from '../hooks/usePerformanceMode';
import { lazy3D, Suspense3D } from '../lib/lazy-3d';
import { apiPost } from '../lib/api';
import { Toast } from '../components/Toast';
import {
  Play,
  Loader2,
  Search,
  Brain,
  BarChart3,
  MessageSquare,
  Send,
  Target,
  Heart,
  UserPlus,
  Clock,
} from 'lucide-react';
import type { PipelineFlowData } from '../pipeline/types';

const PipelineScene = lazy3D<{ data: PipelineFlowData }>(
  () => import('../scenes/PipelineScene'),
);

type ViewMode = '2d' | '3d';

interface PipelineRunResponse {
  status: string;
  message: string;
}

const PIPELINE_STEPS = [
  {
    icon: Search,
    title: 'Collect',
    description: 'Scans Twitter for tweets matching your keywords and ICP filters',
    color: '#3b82f6',
  },
  {
    icon: Brain,
    title: 'Judge',
    description: 'LLM evaluates each tweet for relevance to your product',
    color: '#8b5cf6',
  },
  {
    icon: BarChart3,
    title: 'Score',
    description: 'Weighted scoring (0-100) based on authority, engagement, intent, and recency',
    color: '#f59e0b',
  },
  {
    icon: MessageSquare,
    title: 'Draft',
    description: 'AI generates personalized reply using your persona and tone',
    color: '#ec4899',
  },
  {
    icon: Target,
    title: 'Approve',
    description: 'You review every reply before it goes out — edit, approve, or reject',
    color: '#22c55e',
  },
  {
    icon: Send,
    title: 'Send',
    description: 'Approved replies are posted via your connected Twitter account',
    color: '#06b6d4',
  },
];

const SEQUENCE_STEPS = [
  { icon: Heart, label: 'Like their tweet', delay: 'Instant' },
  { icon: UserPlus, label: 'Follow the user', delay: '+6 hours' },
  { icon: Clock, label: 'Wait for natural timing', delay: '+24 hours' },
  { icon: MessageSquare, label: 'Reply with AI draft', delay: 'After approval' },
  { icon: Target, label: 'Track response', delay: '+3 days' },
];

export default function PipelineLive() {
  const data = usePipelineFlow();
  const { performanceMode } = usePerformanceMode();
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    return (localStorage.getItem('pipeline-view-mode') as ViewMode) || '2d';
  });
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const runPipeline = useMutation({
    mutationFn: () => apiPost<PipelineRunResponse>('/api/pipeline/run'),
    onSuccess: (res) => {
      setToast({ message: res.message || 'Pipeline run started successfully', type: 'success' });
    },
    onError: (err) => {
      setToast({
        message: err instanceof Error ? err.message : 'Failed to start pipeline',
        type: 'error',
      });
    },
  });

  const dismissToast = useCallback(() => setToast(null), []);

  function toggleView(mode: ViewMode) {
    setViewMode(mode);
    localStorage.setItem('pipeline-view-mode', mode);
  }

  return (
    <div className="flex h-full flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--cyber-text)' }}>
          How It Works
        </h1>
        <p className="mt-1 text-sm text-cyber-text-dim">
          Syntrix finds leads on Twitter, scores them with AI, and helps you reach out — all on autopilot.
        </p>
      </div>

      {/* Pipeline Steps — visual explainer */}
      <div className="grid grid-cols-6 gap-2">
        {PIPELINE_STEPS.map((step, i) => (
          <div
            key={step.title}
            className="group relative flex flex-col items-center rounded-lg p-3 text-center transition-all duration-200 hover:scale-[1.03]"
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {/* Connector arrow */}
            {i < PIPELINE_STEPS.length - 1 && (
              <span
                className="absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-cyber-text-dim/40 text-xs"
              >
                &#8250;
              </span>
            )}
            <div
              className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg transition-all duration-200"
              style={{
                background: `${step.color}15`,
                border: `1px solid ${step.color}30`,
              }}
            >
              <step.icon size={16} style={{ color: step.color }} />
            </div>
            <span className="text-xs font-semibold text-cyber-text">{step.title}</span>
            <span className="mt-1 text-[10px] leading-tight text-cyber-text-dim">
              {step.description}
            </span>
          </div>
        ))}
      </div>

      {/* Visualization + Controls */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-cyber-text">Live Pipeline View</h2>
            <span
              className="flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-mono"
              style={{
                background: data.isLive
                  ? 'rgba(34, 197, 94, 0.15)'
                  : 'rgba(107, 114, 128, 0.15)',
                color: data.isLive ? '#22c55e' : '#6b7280',
                border: `1px solid ${data.isLive ? 'rgba(34, 197, 94, 0.3)' : 'rgba(107, 114, 128, 0.3)'}`,
              }}
            >
              <span
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{
                  background: data.isLive ? '#22c55e' : '#6b7280',
                  boxShadow: data.isLive ? '0 0 6px #22c55e' : 'none',
                }}
              />
              {data.isLive ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Run Pipeline button */}
            <button
              type="button"
              onClick={() => runPipeline.mutate()}
              disabled={runPipeline.isPending}
              className="inline-flex items-center gap-2 rounded-md border border-cyber-pink bg-cyber-pink/10 px-4 py-1.5 text-sm font-mono font-semibold text-cyber-pink transition-all duration-200 hover:bg-cyber-pink/20 hover:shadow-[0_0_12px_rgba(255,20,147,0.4)] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {runPipeline.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play size={14} />
                  Run Pipeline
                </>
              )}
            </button>

            {/* 2D / 3D Toggle */}
            <div
              className="glass flex rounded-lg p-0.5"
              role="radiogroup"
              aria-label="View mode"
            >
              <button
                type="button"
                role="radio"
                aria-checked={viewMode === '2d'}
                onClick={() => toggleView('2d')}
                className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                style={{
                  background: viewMode === '2d' ? 'var(--cyber-pink)' : 'transparent',
                  color: viewMode === '2d' ? '#fff' : 'var(--cyber-text-dim)',
                }}
              >
                2D
              </button>
              <button
                type="button"
                role="radio"
                aria-checked={viewMode === '3d'}
                onClick={() => toggleView('3d')}
                disabled={performanceMode}
                className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                style={{
                  background: viewMode === '3d' && !performanceMode ? 'var(--cyber-pink)' : 'transparent',
                  color: viewMode === '3d' && !performanceMode ? '#fff' : 'var(--cyber-text-dim)',
                  opacity: performanceMode ? 0.4 : 1,
                  cursor: performanceMode ? 'not-allowed' : 'pointer',
                }}
                title={performanceMode ? 'Disabled in Performance Mode' : undefined}
              >
                3D
              </button>
            </div>
          </div>
        </div>

        {/* Main visualization + activity feed */}
        <div className="flex gap-4" style={{ minHeight: 380 }}>
          <div className="flex-1 rounded-lg overflow-hidden glass">
            {viewMode === '2d' || performanceMode ? (
              <PipelineDAG data={data} />
            ) : (
              <Suspense3D
                fallback={
                  <div
                    className="flex h-full items-center justify-center font-mono text-sm"
                    style={{ color: 'var(--cyber-text-dim)' }}
                  >
                    Loading 3D scene...
                  </div>
                }
              >
                <PipelineScene data={data} />
              </Suspense3D>
            )}
          </div>

          <div className="w-72 shrink-0">
            <ActivityFeed events={data.events} isLive={data.isLive} />
          </div>
        </div>
      </div>

      {/* Automated Sequences explainer */}
      <div
        className="rounded-lg p-5"
        style={{
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <h2 className="text-sm font-semibold text-cyber-text mb-1">
          Automated Outreach Sequences
        </h2>
        <p className="text-xs text-cyber-text-dim mb-4">
          Once the pipeline scores a lead, sequences handle the outreach automatically — like, follow, wait, then reply.
        </p>
        <div className="flex items-center gap-1">
          {SEQUENCE_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-1">
              <div
                className="flex flex-col items-center rounded-md px-3 py-2 text-center"
                style={{
                  background: 'rgba(255,20,147,0.06)',
                  border: '1px solid rgba(255,20,147,0.15)',
                  minWidth: 100,
                }}
              >
                <step.icon size={14} className="mb-1 text-cyber-pink" />
                <span className="text-[10px] font-medium text-cyber-text">{step.label}</span>
                <span className="text-[9px] text-cyber-text-dim">{step.delay}</span>
              </div>
              {i < SEQUENCE_STEPS.length - 1 && (
                <span className="text-cyber-text-dim/40 text-xs px-0.5">&#8594;</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={dismissToast} />
      )}
    </div>
  );
}
