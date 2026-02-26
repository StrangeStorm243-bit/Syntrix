import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../lib/api';

export interface SequenceStep {
  order: number;
  action_type: string;
  delay_hours: number;
  template: string | null;
}

export interface Sequence {
  id: number;
  name: string;
  description: string;
  steps: SequenceStep[];
  enrolled_count: number;
  active_count: number;
  completed_count: number;
  created_at: string;
  is_active: boolean;
}

export interface Enrollment {
  id: number;
  sequence_id: number;
  lead_id: number;
  author_username: string | null;
  current_step: number;
  status: string;
  started_at: string;
  completed_at: string | null;
}

interface SequencesResponse {
  items: Sequence[];
  total: number;
}

interface EnrollmentsResponse {
  items: Enrollment[];
  total: number;
}

export function useSequences() {
  return useQuery({
    queryKey: ['sequences'],
    queryFn: () => apiGet<SequencesResponse>('/api/sequences'),
    refetchInterval: 10_000,
  });
}

export function useEnrollments(sequenceId: number | null) {
  return useQuery({
    queryKey: ['sequences', sequenceId, 'enrollments'],
    queryFn: () =>
      apiGet<EnrollmentsResponse>(`/api/sequences/${sequenceId}/enrollments`),
    enabled: sequenceId !== null,
  });
}
