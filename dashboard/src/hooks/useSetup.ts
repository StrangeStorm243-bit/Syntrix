import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../lib/api';

export interface SetupStatus {
  is_complete: boolean;
  completed_at: string | null;
  project_id: string | null;
}

interface TestConnectionRequest {
  username: string;
  password: string;
}

interface TestConnectionResponse {
  success: boolean;
  message: string;
}

export interface SetupRequest {
  company: {
    name: string;
    url: string;
    description: string;
    problem_statement: string;
  };
  icp: {
    role_keywords: string[];
    tweet_topics: string[];
    min_followers: number;
    languages: string[];
  };
  twitter: {
    username: string;
    password: string;
  };
  persona: {
    name: string;
    role: string;
    tone: string;
    voice_notes: string;
    example_reply: string;
  };
  llm: {
    provider: string;
    model: string;
    api_key: string;
  };
  outreach: {
    sequence_template: string;
    max_actions_per_day: number;
    require_approval: boolean;
  };
}

interface SetupResponse {
  project_id: string;
  message: string;
}

export function useSetupStatus() {
  return useQuery({
    queryKey: ['setup', 'status'],
    queryFn: () => apiGet<SetupStatus>('/api/setup/status'),
    retry: false,
    staleTime: 60_000,
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: (data: TestConnectionRequest) =>
      apiPost<TestConnectionResponse>('/api/setup/test-connection', data),
  });
}

export function useCompleteSetup() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SetupRequest) =>
      apiPost<SetupResponse>('/api/setup', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['setup', 'status'] });
    },
  });
}
