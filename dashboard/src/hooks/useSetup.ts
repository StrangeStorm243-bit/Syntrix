import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPut } from '../lib/api';

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
  // Step 1: Company
  project_name: string;
  product_url: string;
  description: string;
  problem_statement: string;
  // Step 2: ICP
  role_keywords: string[];
  tweet_topics: string[];
  min_followers: number;
  languages: string[];
  // Step 3: Twitter
  twitter_username: string;
  twitter_password: string;
  x_api_key?: string | null;
  // Step 4: Persona + LLM
  persona_name: string;
  persona_role: string;
  persona_tone: string;
  voice_notes: string;
  example_reply: string;
  llm_provider: string;
  llm_api_key?: string | null;
  // Step 5: Outreach
  sequence_template: string;
  max_actions_per_day: number;
  require_approval: boolean;
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

export interface SettingsUpdateRequest {
  twitter_username?: string | null;
  twitter_password?: string | null;
  llm_provider?: string | null;
  llm_api_key?: string | null;
  max_actions_per_day?: number | null;
  require_approval?: boolean | null;
}

interface SettingsUpdateResponse {
  success: boolean;
  message: string;
}

export function useUpdateSettings() {
  return useMutation({
    mutationFn: (data: SettingsUpdateRequest) =>
      apiPut<SettingsUpdateResponse>('/api/settings', data),
  });
}
