import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../lib/api';

export interface PipelineStats {
  collected: number;
  judged: number;
  relevant: number;
  scored: number;
  drafted: number;
  approved: number;
  sent: number;
  outcomes: number;
}

export function useStats(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['stats', projectId],
    queryFn: () => apiGet<PipelineStats>('/api/stats', params),
  });
}
