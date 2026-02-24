import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../lib/api';

export interface Experiment {
  id: number;
  experiment_id: string;
  project_id: string | null;
  primary_model: string;
  canary_model: string;
  canary_pct: number;
  status: string;
  started_at: string | null;
  ended_at: string | null;
}

export function useExperiments(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['experiments', projectId],
    queryFn: () => apiGet<Experiment[]>('/api/experiments', params),
  });
}
