import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { usePipelineFlow } from '../hooks/usePipelineFlow';
import { PipelineDAG } from '../pipeline/PipelineDAG';
import { ActivityFeed } from '../pipeline/ActivityFeed';
import { usePerformanceMode } from '../hooks/usePerformanceMode';
import { lazy3D, Suspense3D } from '../lib/lazy-3d';
import { apiPost } from '../lib/api';
import { Toast } from '../components/Toast';
import { Play, Loader2 } from 'lucide-react';
import type { PipelineFlowData } from '../pipeline/types';

const PipelineScene = lazy3D<{ data: PipelineFlowData }>(
  () => import('../scenes/PipelineScene'),
);

type ViewMode = '2d' | '3d';

interface PipelineRunResponse {
  status: string;
  message: string;
}

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
    <div className="flex h-full flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--cyber-text)' }}>
            Pipeline Live
          </h1>
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
              className="inline-block h-2 w-2 rounded-full"
              style={{
                background: data.isLive ? '#22c55e' : '#6b7280',
                boxShadow: data.isLive ? '0 0 6px #22c55e' : 'none',
              }}
            />
            {data.isLive ? 'CONNECTED' : 'OFFLINE'}
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

      {/* Main content */}
      <div className="flex flex-1 gap-4 min-h-0">
        {/* Visualization */}
        <div className="flex-1 rounded-lg overflow-hidden glass" style={{ minHeight: 400 }}>
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

        {/* Activity Feed sidebar */}
        <div className="w-80 shrink-0">
          <ActivityFeed events={data.events} isLive={data.isLive} />
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={dismissToast} />
      )}
    </div>
  );
}
