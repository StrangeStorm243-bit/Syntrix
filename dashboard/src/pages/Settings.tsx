import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getStoredApiKey, setApiKey, apiPost } from '../lib/api';
import { GlassCard } from '../components/cyber/GlassCard';
import { NeonInput } from '../components/cyber/NeonInput';
import { NeonButton } from '../components/cyber/NeonButton';
import { usePerformanceMode } from '../hooks/usePerformanceMode';
import { useUpdateSettings } from '../hooks/useSetup';
import type { SettingsUpdateRequest } from '../hooks/useSetup';
import { Toast } from '../components/Toast';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Twitter,
  Brain,
  Zap,
  Check,
  Loader2,
  Key,
  Shield,
  Save,
  Clock,
} from 'lucide-react';

interface TestConnectionResponse {
  success: boolean;
  message: string;
}

const PROVIDER_OPTIONS = [
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
];

export default function Settings() {
  // API Key
  const [key, setKey] = useState(getStoredApiKey());
  const [saved, setSaved] = useState(false);
  const { performanceMode, toggle } = usePerformanceMode();

  // Twitter credentials
  const [twitterUsername, setTwitterUsername] = useState('');
  const [twitterPassword, setTwitterPassword] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const testConnection = useMutation({
    mutationFn: (data: { username: string; password: string }) =>
      apiPost<TestConnectionResponse>('/api/setup/test-connection', data),
    onSuccess: (res) => {
      setToast({
        message: res.success ? 'Connection verified!' : (res.message || 'Connection failed'),
        type: res.success ? 'success' : 'error',
      });
    },
    onError: (err) => {
      setToast({
        message: err instanceof Error ? err.message : 'Connection test failed',
        type: 'error',
      });
    },
  });

  // LLM config
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [llmModel, setLlmModel] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');

  // Sequence settings
  const [maxActionsPerDay, setMaxActionsPerDay] = useState(20);
  const [requireApproval, setRequireApproval] = useState(true);
  const [pipelineInterval, setPipelineInterval] = useState(4);

  const updateSettings = useUpdateSettings();

  const dismissToast = useCallback(() => setToast(null), []);

  function handleSaveSettings() {
    const payload: SettingsUpdateRequest = {
      twitter_username: twitterUsername || null,
      twitter_password: twitterPassword || null,
      llm_provider: llmProvider,
      llm_api_key: llmApiKey || null,
      max_actions_per_day: maxActionsPerDay,
      require_approval: requireApproval,
      pipeline_interval_hours: pipelineInterval,
    };
    updateSettings.mutate(payload, {
      onSuccess: (res) => {
        setToast({
          message: res.success ? 'Settings saved successfully!' : (res.message || 'Save failed'),
          type: res.success ? 'success' : 'error',
        });
      },
      onError: (err) => {
        setToast({
          message: err instanceof Error ? err.message : 'Failed to save settings',
          type: 'error',
        });
      },
    });
  }

  function handleSaveApiKey() {
    setApiKey(key);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-cyber-text">Settings</h1>

      <div className="max-w-2xl space-y-6">
        {/* API Key */}
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Key size={16} className="text-cyber-pink" />
            <h2 className="text-sm font-medium text-cyber-text">API Configuration</h2>
          </div>
          <div className="space-y-4">
            <NeonInput
              label="API Key"
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Enter your Syntrix API key"
            />
            <NeonButton onClick={handleSaveApiKey}>
              {saved ? 'Saved!' : 'Save'}
            </NeonButton>
          </div>
        </GlassCard>

        {/* Twitter Credentials */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Twitter size={16} className="text-cyber-pink" />
              <CardTitle className="text-cyber-text text-sm">Twitter Credentials</CardTitle>
            </div>
            <CardDescription className="text-cyber-text-dim text-xs">
              Credentials used to authenticate with the Twitter API for collecting and posting tweets.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-cyber-text-dim text-sm">Username</Label>
              <Input
                value={twitterUsername}
                onChange={(e) => setTwitterUsername(e.target.value)}
                placeholder="@username"
                className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-cyber-text-dim text-sm">Password</Label>
              <Input
                type="password"
                value={twitterPassword}
                onChange={(e) => setTwitterPassword(e.target.value)}
                placeholder="Your Twitter password"
                className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
              />
            </div>
            <button
              type="button"
              onClick={() =>
                testConnection.mutate({ username: twitterUsername, password: twitterPassword })
              }
              disabled={!twitterUsername || !twitterPassword || testConnection.isPending}
              className="inline-flex items-center gap-2 rounded-md border border-cyber-pink bg-cyber-pink/10 px-4 py-2 text-sm font-mono font-semibold text-cyber-pink transition-all duration-200 hover:bg-cyber-pink/20 hover:shadow-[0_0_12px_rgba(255,20,147,0.4)] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {testConnection.isPending ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Testing...
                </>
              ) : testConnection.isSuccess && testConnection.data.success ? (
                <>
                  <Check size={14} className="text-green-400" />
                  Verified
                </>
              ) : (
                <>
                  <Twitter size={14} />
                  Test Connection
                </>
              )}
            </button>
          </CardContent>
        </Card>

        {/* LLM Configuration */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain size={16} className="text-cyber-pink" />
              <CardTitle className="text-cyber-text text-sm">LLM Configuration</CardTitle>
            </div>
            <CardDescription className="text-cyber-text-dim text-xs">
              Configure which language model to use for judging leads and drafting replies.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-cyber-text-dim text-sm">Provider</Label>
              <Select value={llmProvider} onValueChange={setLlmProvider}>
                <SelectTrigger className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text focus:border-cyber-pink/60 focus:ring-cyber-pink/25">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-cyber-pink/20 bg-cyber-surface backdrop-blur-xl">
                  {PROVIDER_OPTIONS.map((p) => (
                    <SelectItem
                      key={p.value}
                      value={p.value}
                      className="font-mono text-cyber-text focus:bg-cyber-pink/10 focus:text-cyber-pink"
                    >
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-cyber-text-dim text-sm">Model Name</Label>
              <Input
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                placeholder={llmProvider === 'ollama' ? 'llama3.1' : 'gpt-4o-mini'}
                className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
              />
            </div>
            {llmProvider !== 'ollama' && (
              <div className="space-y-2">
                <Label className="text-cyber-text-dim text-sm">API Key</Label>
                <Input
                  type="password"
                  value={llmApiKey}
                  onChange={(e) => setLlmApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sequence Settings */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-cyber-pink" />
              <CardTitle className="text-cyber-text text-sm">Sequence Settings</CardTitle>
            </div>
            <CardDescription className="text-cyber-text-dim text-xs">
              Control how outreach sequences behave.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-cyber-text-dim text-sm">Max Actions Per Day</Label>
                <span className="rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink">
                  {maxActionsPerDay}
                </span>
              </div>
              <Slider
                value={[maxActionsPerDay]}
                onValueChange={(v) => setMaxActionsPerDay(v[0])}
                min={5}
                max={100}
                step={5}
                className="[&_[data-slot=slider-track]]:bg-cyber-surface-bright [&_[data-slot=slider-range]]:bg-cyber-pink [&_[data-slot=slider-thumb]]:border-cyber-pink [&_[data-slot=slider-thumb]]:bg-cyber-void"
              />
              <p className="text-[10px] text-cyber-text-dim/70">
                Rate limit for total actions (likes, replies, follows) per day.
              </p>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-white/5 bg-cyber-surface/30 p-3">
              <div>
                <p className="text-sm text-cyber-text">Require Approval</p>
                <p className="mt-0.5 text-xs text-cyber-text-dim">
                  Review and approve each reply before it is sent
                </p>
              </div>
              <Switch
                checked={requireApproval}
                onCheckedChange={setRequireApproval}
                className="data-[state=checked]:bg-cyber-pink"
              />
            </div>
          </CardContent>
        </Card>

        {/* Pipeline Auto-Run */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-cyber-pink" />
              <CardTitle className="text-cyber-text text-sm">Pipeline Auto-Run</CardTitle>
            </div>
            <CardDescription className="text-cyber-text-dim text-xs">
              How often the pipeline automatically collects and scores new leads.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-cyber-text-dim text-sm">Run Every</Label>
              <span className="rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink">
                {pipelineInterval}h
              </span>
            </div>
            <Slider
              value={[pipelineInterval]}
              onValueChange={(v) => setPipelineInterval(v[0])}
              min={1}
              max={24}
              step={1}
              className="[&_[data-slot=slider-track]]:bg-cyber-surface-bright [&_[data-slot=slider-range]]:bg-cyber-pink [&_[data-slot=slider-thumb]]:border-cyber-pink [&_[data-slot=slider-thumb]]:bg-cyber-void"
            />
            <p className="text-[10px] text-cyber-text-dim/70">
              Pipeline collects tweets, judges relevance, scores leads, and generates drafts automatically.
            </p>
          </CardContent>
        </Card>

        {/* Save Settings */}
        <button
          type="button"
          onClick={handleSaveSettings}
          disabled={updateSettings.isPending}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-cyber-pink bg-cyber-pink/10 px-6 py-3 text-sm font-mono font-semibold text-cyber-pink transition-all duration-200 hover:bg-cyber-pink/20 hover:shadow-[0_0_16px_rgba(255,20,147,0.4)] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {updateSettings.isPending ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Saving...
            </>
          ) : updateSettings.isSuccess ? (
            <>
              <Check size={16} className="text-green-400" />
              Saved!
            </>
          ) : (
            <>
              <Save size={16} />
              Save Settings
            </>
          )}
        </button>

        {/* Performance Mode */}
        <GlassCard>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield size={16} className="text-cyber-pink" />
              <div>
                <h2 className="text-sm font-medium text-cyber-text">Performance Mode</h2>
                <p className="mt-1 text-xs text-cyber-text-dim">
                  Disable 3D scenes and particles for better performance on low-end devices.
                </p>
              </div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={performanceMode}
              onClick={toggle}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-pink ${
                performanceMode ? 'bg-cyber-pink' : 'bg-cyber-surface-bright'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-cyber-text shadow-lg transition-transform duration-200 ${
                  performanceMode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </GlassCard>
      </div>

      {/* Toast notification */}
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={dismissToast} />
      )}
    </div>
  );
}
