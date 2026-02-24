import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../lib/api';

export interface DraftItem {
  id: number;
  normalized_post_id: number;
  project_id: string;
  text_generated: string;
  text_final: string | null;
  tone: string | null;
  template_used: string | null;
  model_id: string;
  status: string;
  created_at: string | null;
  approved_at: string | null;
  sent_at: string | null;
  author_username: string | null;
  author_display_name: string | null;
  text_original: string | null;
  score: number | null;
}

interface PaginatedDrafts {
  items: DraftItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useQueue(params: Record<string, string> = {}) {
  return useQuery({
    queryKey: ['queue', params],
    queryFn: () => apiGet<PaginatedDrafts>('/api/queue', params),
  });
}

export function useApproveDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (draftId: number) => apiPost<DraftItem>(`/api/queue/${draftId}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['queue'] }),
  });
}

export function useEditDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) =>
      apiPost<DraftItem>(`/api/queue/${id}/edit`, { text }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['queue'] }),
  });
}

export function useRejectDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      apiPost<DraftItem>(`/api/queue/${id}/reject`, { reason: reason || '' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['queue'] }),
  });
}
