import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../lib/api';

interface ScoreBucket {
  bucket_min: number;
  bucket_max: number;
  count: number;
}

interface FunnelStep {
  stage: string;
  count: number;
}

interface QueryPerf {
  query_label: string;
  total_leads: number;
  avg_score: number;
  relevant_pct: number;
}

export function useScoreDistribution(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['analytics', 'score-distribution', projectId],
    queryFn: () => apiGet<ScoreBucket[]>('/api/analytics/score-distribution', params),
  });
}

export function useConversionFunnel(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['analytics', 'funnel', projectId],
    queryFn: () => apiGet<FunnelStep[]>('/api/analytics/conversion-funnel', params),
  });
}

export function useQueryPerformance(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['analytics', 'query-performance', projectId],
    queryFn: () => apiGet<QueryPerf[]>('/api/analytics/query-performance', params),
  });
}

interface PersonaEffectiveness {
  tone: string;
  template_used: string | null;
  total_drafts: number;
  approved_count: number;
  rejected_count: number;
  approval_rate: number;
}

export function usePersonaEffectiveness(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['analytics', 'persona-effectiveness', projectId],
    queryFn: () => apiGet<PersonaEffectiveness[]>('/api/analytics/persona-effectiveness', params),
  });
}
