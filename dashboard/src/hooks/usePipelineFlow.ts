import { useCallback, useEffect, useRef, useState } from 'react';
import { useStats } from './useStats';
import { useWebSocket } from './useWebSocket';
import type {
  PipelineEdge,
  PipelineEvent,
  PipelineFlowData,
  PipelineStage,
} from '../pipeline/types';

const STAGE_DEFS: Omit<PipelineStage, 'count' | 'active'>[] = [
  { id: 'collect', label: 'Collect', color: '#ff1493' },
  { id: 'judge', label: 'Judge', color: '#ff6b35' },
  { id: 'score', label: 'Score', color: '#ffd700' },
  { id: 'draft', label: 'Draft', color: '#ff1493' },
  { id: 'send', label: 'Send', color: '#ff6b35' },
  { id: 'dm', label: 'DM', color: '#a855f7' },
];

const STATS_KEY_MAP: Record<string, string> = {
  collect: 'collected',
  judge: 'judged',
  score: 'scored',
  draft: 'drafted',
  send: 'sent',
  dm: 'dms_sent',
};

const MAX_EVENTS = 50;
const THROTTLE_MS = 200; // 5 events/sec max

export function usePipelineFlow(projectId?: string): PipelineFlowData {
  const { data: stats } = useStats(projectId);
  const { lastMessage, connected } = useWebSocket();
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const lastEventTime = useRef(0);

  const addEvent = useCallback((event: PipelineEvent) => {
    const now = Date.now();
    if (now - lastEventTime.current < THROTTLE_MS) return;
    lastEventTime.current = now;
    setEvents((prev) => [event, ...prev].slice(0, MAX_EVENTS));
  }, []);

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'pipeline_progress') return;

    const event: PipelineEvent = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type: 'item_completed',
      stage: lastMessage.stage,
      timestamp: Date.now(),
      detail: lastMessage.detail,
    };
    addEvent(event);
  }, [lastMessage, addEvent]);

  const statsRecord = stats as unknown as Record<string, number> | undefined;

  const stages: PipelineStage[] = STAGE_DEFS.map((def) => ({
    ...def,
    count: statsRecord?.[STATS_KEY_MAP[def.id]] ?? 0,
    active: lastMessage?.type === 'pipeline_progress' && lastMessage.stage === def.id,
  }));

  const edges: PipelineEdge[] = stages.slice(0, -1).map((s, i) => ({
    source: s.id,
    target: stages[i + 1].id,
    throughput: Math.min(s.count, stages[i + 1].count),
    animated: true,
  }));

  return { stages, edges, events, isLive: connected };
}
