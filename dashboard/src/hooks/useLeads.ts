import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../lib/api';

export interface Lead {
  id: number;
  platform: string;
  platform_id: string;
  author_username: string | null;
  author_display_name: string | null;
  author_followers: number;
  author_verified: boolean;
  text_original: string;
  text_cleaned: string;
  created_at: string;
  score: number | null;
  judgment_label: string | null;
  judgment_confidence: number | null;
  draft_status: string | null;
}

export interface PaginatedLeads {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useLeads(params: Record<string, string> = {}) {
  return useQuery({
    queryKey: ['leads', params],
    queryFn: () => apiGet<PaginatedLeads>('/api/leads', params),
  });
}

export function useTopLeads(projectId?: string) {
  const params: Record<string, string> = {};
  if (projectId) params.project_id = projectId;
  return useQuery({
    queryKey: ['leads', 'top', projectId],
    queryFn: () => apiGet<Lead[]>('/api/leads/top', params),
  });
}
