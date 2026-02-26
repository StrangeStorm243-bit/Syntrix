import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Building2,
  Target,
  Twitter,
  User,
  Zap,
  ArrowRight,
  ArrowLeft,
  Check,
  Loader2,
  X,
  Sparkles,
} from 'lucide-react';
import { Progress } from '../components/ui/progress';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
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
import { useWizardStore } from '../stores/wizardStore';
import { useTestConnection, useCompleteSetup } from '../hooks/useSetup';
import type { SetupRequest } from '../hooks/useSetup';

const STEPS = [
  { label: 'Company', icon: Building2, subtitle: 'Tell us about your product so AI can find relevant leads' },
  { label: 'ICP', icon: Target, subtitle: 'Define your ideal customer profile to filter the right people' },
  { label: 'Twitter', icon: Twitter, subtitle: 'Connect your Twitter account to collect tweets and send replies' },
  { label: 'Persona', icon: User, subtitle: 'Configure your AI reply persona and choose your LLM provider' },
  { label: 'Outreach', icon: Zap, subtitle: 'Pick an outreach sequence and set your daily action limits' },
];

const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'witty', label: 'Witty' },
  { value: 'casual', label: 'Casual' },
  { value: 'technical', label: 'Technical' },
];

const PROVIDER_OPTIONS = [
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
];

const SEQUENCE_TEMPLATES = [
  {
    id: 'engage-then-pitch',
    name: 'Engage Then Pitch',
    description:
      'Like their tweet, reply with value, then follow up with a DM after engagement.',
    steps: ['Like Tweet', 'Value Reply', 'Follow', 'DM Follow-Up'],
  },
  {
    id: 'direct-value',
    name: 'Direct Value',
    description:
      'Lead with a helpful reply that naturally mentions your product, then DM after engagement.',
    steps: ['Value Reply', 'Check Engagement', 'DM Resource'],
  },
  {
    id: 'relationship-first',
    name: 'Relationship First',
    description:
      'Build genuine rapport over multiple interactions before any mention of your product.',
    steps: ['Like Tweet', 'Thoughtful Reply', 'Follow', 'Engage Again', 'DM Soft Pitch'],
  },
  {
    id: 'cold-dm',
    name: 'Cold DM',
    description:
      'Send a direct message immediately after finding a relevant lead. Lands in message requests for non-followers.',
    steps: ['DM Outreach'],
  },
];

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
];

/** Reusable tag input for arrays of strings */
function TagInput({
  tags,
  onAdd,
  onRemove,
  placeholder,
}: {
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState('');

  function handleKeyDown(e: React.KeyboardEvent) {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault();
      onAdd(input.trim());
      setInput('');
    }
    if (e.key === 'Backspace' && !input && tags.length > 0) {
      onRemove(tags.length - 1);
    }
  }

  return (
    <div className="flex flex-wrap gap-2 rounded-md border border-cyber-pink/20 bg-cyber-surface/50 p-2 backdrop-blur-sm focus-within:border-cyber-pink/60 focus-within:shadow-[0_0_0_1px_rgba(255,20,147,0.4),0_0_12px_rgba(255,20,147,0.25)] transition-shadow duration-200">
      {tags.map((tag, i) => (
        <span
          key={`${tag}-${i}`}
          className="inline-flex items-center gap-1 rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink"
        >
          {tag}
          <button
            type="button"
            onClick={() => onRemove(i)}
            className="ml-0.5 rounded-full p-0.5 hover:bg-cyber-pink/20 transition-colors"
          >
            <X size={10} />
          </button>
        </span>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="min-w-[120px] flex-1 bg-transparent text-sm font-mono text-cyber-text outline-none placeholder:text-cyber-text-dim/50"
      />
    </div>
  );
}

function StepCompany() {
  const { companyName, companyUrl, companyDescription, problemStatement, updateField } =
    useWizardStore();

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Company Name</Label>
        <Input
          value={companyName}
          onChange={(e) => updateField('companyName', e.target.value)}
          placeholder="Acme Corp"
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Product URL</Label>
        <Input
          value={companyUrl}
          onChange={(e) => updateField('companyUrl', e.target.value)}
          placeholder="https://acme.com"
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Description</Label>
        <Textarea
          value={companyDescription}
          onChange={(e) => updateField('companyDescription', e.target.value)}
          placeholder="What does your product do?"
          rows={3}
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Problem Statement</Label>
        <Textarea
          value={problemStatement}
          onChange={(e) => updateField('problemStatement', e.target.value)}
          placeholder="What problem does your product solve for customers?"
          rows={3}
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
    </div>
  );
}

function StepICP() {
  const { roleKeywords, tweetTopics, minFollowers, languages, updateField } =
    useWizardStore();

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Role Keywords</Label>
        <p className="text-xs text-cyber-text-dim/70">
          Job titles or roles your ideal customers have. Press Enter to add.
        </p>
        <TagInput
          tags={roleKeywords}
          onAdd={(tag) => updateField('roleKeywords', [...roleKeywords, tag])}
          onRemove={(i) =>
            updateField(
              'roleKeywords',
              roleKeywords.filter((_, idx) => idx !== i),
            )
          }
          placeholder="e.g. CTO, VP Engineering, DevOps Lead"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Tweet Topics</Label>
        <p className="text-xs text-cyber-text-dim/70">
          Topics your ideal customers tweet about. Press Enter to add.
        </p>
        <TagInput
          tags={tweetTopics}
          onAdd={(tag) => updateField('tweetTopics', [...tweetTopics, tag])}
          onRemove={(i) =>
            updateField(
              'tweetTopics',
              tweetTopics.filter((_, idx) => idx !== i),
            )
          }
          placeholder="e.g. microservices, observability, CI/CD"
        />
      </div>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-cyber-text-dim text-sm">Minimum Followers</Label>
          <span className="rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink">
            {minFollowers.toLocaleString()}
          </span>
        </div>
        <Slider
          value={[minFollowers]}
          onValueChange={(v) => updateField('minFollowers', v[0])}
          min={0}
          max={10000}
          step={100}
          className="[&_[data-slot=slider-track]]:bg-cyber-surface-bright [&_[data-slot=slider-range]]:bg-cyber-pink [&_[data-slot=slider-thumb]]:border-cyber-pink [&_[data-slot=slider-thumb]]:bg-cyber-void"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Languages</Label>
        <div className="flex flex-wrap gap-2">
          {LANGUAGE_OPTIONS.map((lang) => {
            const active = languages.includes(lang.value);
            return (
              <button
                key={lang.value}
                type="button"
                onClick={() => {
                  if (active) {
                    updateField(
                      'languages',
                      languages.filter((l) => l !== lang.value),
                    );
                  } else {
                    updateField('languages', [...languages, lang.value]);
                  }
                }}
                className={`rounded-full border px-3 py-1 text-xs font-mono transition-all duration-200 ${
                  active
                    ? 'border-cyber-pink bg-cyber-pink/15 text-cyber-pink shadow-[0_0_8px_rgba(255,20,147,0.3)]'
                    : 'border-cyber-surface-bright bg-cyber-surface/50 text-cyber-text-dim hover:border-cyber-pink/30 hover:text-cyber-text'
                }`}
              >
                {lang.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StepTwitter() {
  const { twitterUsername, twitterPassword, connectionTested, updateField } =
    useWizardStore();
  const testConnection = useTestConnection();

  function handleTest() {
    testConnection.mutate(
      { username: twitterUsername, password: twitterPassword },
      {
        onSuccess: (data) => {
          if (data.success) {
            updateField('connectionTested', true);
          }
        },
      },
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-cyber-orange/20 bg-cyber-orange/5 p-3">
        <p className="text-xs text-cyber-orange">
          Your credentials are stored locally and used only to authenticate with the Twitter API.
          They are never sent to third parties.
        </p>
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Twitter Username</Label>
        <Input
          value={twitterUsername}
          onChange={(e) => {
            updateField('twitterUsername', e.target.value);
            updateField('connectionTested', false);
          }}
          placeholder="@username"
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Twitter Password</Label>
        <Input
          type="password"
          value={twitterPassword}
          onChange={(e) => {
            updateField('twitterPassword', e.target.value);
            updateField('connectionTested', false);
          }}
          placeholder="Your Twitter password"
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <Button
        onClick={handleTest}
        disabled={!twitterUsername || !twitterPassword || testConnection.isPending}
        className="w-full border border-cyber-pink bg-cyber-pink/10 font-mono text-cyber-pink hover:bg-cyber-pink/20 hover:shadow-[0_0_12px_rgba(255,20,147,0.4)] disabled:opacity-40 disabled:cursor-not-allowed"
        variant="outline"
      >
        {testConnection.isPending ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Testing Connection...
          </>
        ) : connectionTested ? (
          <>
            <Check size={16} className="text-green-400" />
            Connection Verified
          </>
        ) : (
          <>
            <Twitter size={16} />
            Test Connection
          </>
        )}
      </Button>
      {testConnection.isError && (
        <p className="text-xs text-red-400">
          Connection failed. Please check your credentials.
        </p>
      )}
      {connectionTested && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 p-3"
        >
          <Check size={14} className="text-green-400" />
          <span className="text-xs text-green-400">
            Successfully connected to Twitter API
          </span>
        </motion.div>
      )}
    </div>
  );
}

function StepPersona() {
  const {
    personaName,
    personaRole,
    personaTone,
    voiceNotes,
    exampleReply,
    llmProvider,
    llmModel,
    llmApiKey,
    updateField,
  } = useWizardStore();

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className="text-cyber-text-dim text-sm">Persona Name</Label>
          <Input
            value={personaName}
            onChange={(e) => updateField('personaName', e.target.value)}
            placeholder="Alex"
            className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-cyber-text-dim text-sm">Role</Label>
          <Input
            value={personaRole}
            onChange={(e) => updateField('personaRole', e.target.value)}
            placeholder="Developer Advocate"
            className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Tone</Label>
        <Select value={personaTone} onValueChange={(v) => updateField('personaTone', v)}>
          <SelectTrigger className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text focus:border-cyber-pink/60 focus:ring-cyber-pink/25">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="border-cyber-pink/20 bg-cyber-surface backdrop-blur-xl">
            {TONE_OPTIONS.map((t) => (
              <SelectItem
                key={t.value}
                value={t.value}
                className="font-mono text-cyber-text focus:bg-cyber-pink/10 focus:text-cyber-pink"
              >
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Voice Notes</Label>
        <Textarea
          value={voiceNotes}
          onChange={(e) => updateField('voiceNotes', e.target.value)}
          placeholder="How should replies sound? e.g. 'Always lead with empathy, use technical jargon sparingly'"
          rows={2}
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>
      <div className="space-y-2">
        <Label className="text-cyber-text-dim text-sm">Example Reply</Label>
        <Textarea
          value={exampleReply}
          onChange={(e) => updateField('exampleReply', e.target.value)}
          placeholder="Write an example reply that captures the tone you want..."
          rows={2}
          className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
        />
      </div>

      <div className="mt-2 border-t border-white/10 pt-4">
        <h3 className="mb-3 text-sm font-medium text-cyber-text">LLM Configuration</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-cyber-text-dim text-sm">Provider</Label>
            <Select value={llmProvider} onValueChange={(v) => updateField('llmProvider', v)}>
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
              onChange={(e) => updateField('llmModel', e.target.value)}
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
                onChange={(e) => updateField('llmApiKey', e.target.value)}
                placeholder="sk-..."
                className="glass border-cyber-pink/20 bg-cyber-surface/50 font-mono text-cyber-text placeholder:text-cyber-text-dim/50 focus-visible:border-cyber-pink/60 focus-visible:ring-cyber-pink/25"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StepOutreach() {
  const { sequenceTemplate, maxActionsPerDay, requireApproval, updateField } =
    useWizardStore();

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <Label className="text-cyber-text-dim text-sm">Sequence Template</Label>
        <div className="grid gap-3">
          {SEQUENCE_TEMPLATES.map((tmpl) => {
            const active = sequenceTemplate === tmpl.id;
            return (
              <button
                key={tmpl.id}
                type="button"
                onClick={() => updateField('sequenceTemplate', tmpl.id)}
                className={`group relative rounded-lg border p-4 text-left transition-all duration-200 ${
                  active
                    ? 'border-cyber-pink bg-cyber-pink/10 shadow-[0_0_16px_rgba(255,20,147,0.2)]'
                    : 'border-cyber-surface-bright bg-cyber-surface/50 hover:border-cyber-pink/30'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4
                      className={`text-sm font-semibold ${
                        active ? 'text-cyber-pink' : 'text-cyber-text'
                      }`}
                    >
                      {tmpl.name}
                    </h4>
                    <p className="mt-1 text-xs text-cyber-text-dim">{tmpl.description}</p>
                  </div>
                  {active && (
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyber-pink">
                      <Check size={12} className="text-white" />
                    </span>
                  )}
                </div>
                {/* Step visualization */}
                <div className="mt-3 flex items-center gap-1">
                  {tmpl.steps.map((step, i) => (
                    <div key={step} className="flex items-center gap-1">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-mono ${
                          active
                            ? 'bg-cyber-pink/20 text-cyber-pink'
                            : 'bg-cyber-surface-bright text-cyber-text-dim'
                        }`}
                      >
                        {i + 1}. {step}
                      </span>
                      {i < tmpl.steps.length - 1 && (
                        <ArrowRight
                          size={10}
                          className={active ? 'text-cyber-pink/50' : 'text-cyber-text-dim/30'}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-cyber-text-dim text-sm">Max Actions Per Day</Label>
          <span className="rounded-full border border-cyber-pink/30 bg-cyber-pink/10 px-2.5 py-0.5 text-xs font-mono text-cyber-pink">
            {maxActionsPerDay}
          </span>
        </div>
        <Slider
          value={[maxActionsPerDay]}
          onValueChange={(v) => updateField('maxActionsPerDay', v[0])}
          min={5}
          max={100}
          step={5}
          className="[&_[data-slot=slider-track]]:bg-cyber-surface-bright [&_[data-slot=slider-range]]:bg-cyber-pink [&_[data-slot=slider-thumb]]:border-cyber-pink [&_[data-slot=slider-thumb]]:bg-cyber-void"
        />
        <p className="text-[10px] text-cyber-text-dim/70">
          Rate limit for total actions (likes, replies, follows) per day
        </p>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-cyber-surface-bright bg-cyber-surface/50 p-3">
        <div>
          <p className="text-sm text-cyber-text">Require Approval</p>
          <p className="mt-0.5 text-xs text-cyber-text-dim">
            Review and approve each reply before it is sent
          </p>
        </div>
        <Switch
          checked={requireApproval}
          onCheckedChange={(checked) => updateField('requireApproval', checked)}
          className="data-[state=checked]:bg-cyber-pink"
        />
      </div>
    </div>
  );
}

const STEP_COMPONENTS = [StepCompany, StepICP, StepTwitter, StepPersona, StepOutreach];

export default function Onboarding() {
  const store = useWizardStore();
  const completeSetup = useCompleteSetup();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [setupComplete, setSetupComplete] = useState(false);

  const canProceed = useCallback(() => {
    switch (store.step) {
      case 0:
        return !!store.companyName.trim();
      case 1:
        return store.roleKeywords.length > 0 || store.tweetTopics.length > 0;
      case 2:
        return !!store.twitterUsername.trim() && !!store.twitterPassword.trim();
      case 3:
        return !!store.personaName.trim();
      case 4:
        return !!store.sequenceTemplate;
      default:
        return false;
    }
  }, [store]);

  function handleSubmit() {
    const payload: SetupRequest = {
      project_name: store.companyName,
      product_url: store.companyUrl,
      description: store.companyDescription,
      problem_statement: store.problemStatement,
      role_keywords: store.roleKeywords,
      tweet_topics: store.tweetTopics,
      min_followers: store.minFollowers,
      languages: store.languages,
      twitter_username: store.twitterUsername,
      twitter_password: store.twitterPassword,
      persona_name: store.personaName,
      persona_role: store.personaRole,
      persona_tone: store.personaTone,
      voice_notes: store.voiceNotes,
      example_reply: store.exampleReply,
      llm_provider: store.llmProvider,
      llm_api_key: store.llmApiKey || null,
      sequence_template: store.sequenceTemplate,
      max_actions_per_day: store.maxActionsPerDay,
      require_approval: store.requireApproval,
    };

    setSubmitError(null);
    completeSetup.mutate(payload, {
      onSuccess: () => {
        setSetupComplete(true);
      },
      onError: (err) => {
        setSubmitError(err instanceof Error ? err.message : 'Setup failed. Please try again.');
      },
    });
  }

  const StepComponent = STEP_COMPONENTS[store.step];
  const progressPct = ((store.step + 1) / STEPS.length) * 100;

  if (setupComplete) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cyber-void p-4">
        <div
          className="pointer-events-none fixed inset-0"
          style={{
            background:
              'radial-gradient(ellipse 60% 40% at 50% 40%, rgba(255,20,147,0.12) 0%, transparent 70%)',
          }}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="relative z-10 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200, damping: 15 }}
            className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full"
            style={{
              background: 'rgba(255,20,147,0.15)',
              border: '2px solid rgba(255,20,147,0.5)',
              boxShadow: '0 0 30px rgba(255,20,147,0.3)',
            }}
          >
            <Sparkles size={28} className="text-cyber-pink" />
          </motion.div>
          <h2
            className="text-2xl font-bold tracking-wider text-cyber-pink"
            style={{ textShadow: '0 0 15px var(--cyber-glow-pink)' }}
          >
            Setup Complete!
          </h2>
          <p className="mt-2 text-sm text-cyber-text-dim">
            Launching your dashboard...
          </p>
          <Loader2 size={20} className="mx-auto mt-4 animate-spin text-cyber-pink/60" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-cyber-void p-4">
      {/* Background glow effects */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background:
            'radial-gradient(ellipse 60% 40% at 30% 20%, rgba(255,20,147,0.08) 0%, transparent 70%), radial-gradient(ellipse 50% 50% at 70% 80%, rgba(255,107,53,0.06) 0%, transparent 70%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative z-10 w-full max-w-xl"
      >
        {/* Header */}
        <div className="mb-6 text-center">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-3xl font-bold tracking-widest uppercase text-cyber-pink"
            style={{
              textShadow:
                '0 0 10px var(--cyber-glow-pink), 0 0 30px var(--cyber-glow-pink)',
            }}
          >
            Syntrix
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-2 text-sm text-cyber-text-dim"
          >
            Let&apos;s set up your lead generation pipeline
          </motion.p>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mx-auto mt-3 flex max-w-md flex-wrap justify-center gap-2"
          >
            {['Find leads on Twitter', 'Score with AI', 'Draft replies', 'You approve', 'Auto-send'].map(
              (item, i) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-1 text-[10px] font-mono text-cyber-text-dim/80"
                >
                  {i > 0 && (
                    <span className="text-cyber-pink/40 mr-1">&#8594;</span>
                  )}
                  {item}
                </span>
              ),
            )}
          </motion.div>
        </div>

        {/* Step indicator */}
        <div className="mb-4 flex items-center justify-center gap-3">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            const isActive = i === store.step;
            const isDone = i < store.step;
            return (
              <div key={s.label} className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => i < store.step && store.setStep(i)}
                  disabled={i > store.step}
                  className={`flex h-8 w-8 items-center justify-center rounded-full border transition-all duration-300 ${
                    isActive
                      ? 'border-cyber-pink bg-cyber-pink/20 text-cyber-pink shadow-[0_0_12px_rgba(255,20,147,0.4)]'
                      : isDone
                        ? 'border-cyber-pink/50 bg-cyber-pink/10 text-cyber-pink/70'
                        : 'border-cyber-surface-bright bg-cyber-surface/30 text-cyber-text-dim'
                  } ${i <= store.step ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                >
                  {isDone ? <Check size={14} /> : <Icon size={14} />}
                </button>
                {i < STEPS.length - 1 && (
                  <div
                    className={`h-px w-6 transition-colors duration-300 ${
                      i < store.step ? 'bg-cyber-pink/50' : 'bg-cyber-surface-bright'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <Progress
          value={progressPct}
          className="mb-6 h-1 bg-cyber-surface-bright [&_[data-slot=progress-indicator]]:bg-cyber-pink [&_[data-slot=progress-indicator]]:shadow-[0_0_8px_rgba(255,20,147,0.5)]"
        />

        {/* Card with step content */}
        <Card className="glass border-white/10 bg-cyber-surface/80 backdrop-blur-xl shadow-[0_0_40px_rgba(255,20,147,0.05)]">
          <CardContent className="pt-2">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-cyber-text">
                {STEPS[store.step].label}
              </h2>
              <p className="mt-0.5 text-xs text-cyber-text-dim">
                {STEPS[store.step].subtitle}
              </p>
              <p className="mt-1 text-[10px] text-cyber-text-dim/60 font-mono">
                Step {store.step + 1} of {STEPS.length}
              </p>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={store.step}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
              >
                <StepComponent />
              </motion.div>
            </AnimatePresence>

            {submitError && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 text-xs text-red-400"
              >
                {submitError}
              </motion.p>
            )}

            {/* Navigation */}
            <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4">
              <Button
                onClick={store.prevStep}
                disabled={store.step === 0}
                variant="ghost"
                className="font-mono text-cyber-text-dim hover:text-cyber-text disabled:opacity-30"
              >
                <ArrowLeft size={16} />
                Back
              </Button>

              {store.step < STEPS.length - 1 ? (
                <Button
                  onClick={store.nextStep}
                  disabled={!canProceed()}
                  className="border border-cyber-pink bg-cyber-pink/10 font-mono text-cyber-pink hover:bg-cyber-pink/20 hover:shadow-[0_0_12px_rgba(255,20,147,0.4)] disabled:opacity-40"
                  variant="outline"
                >
                  Next
                  <ArrowRight size={16} />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={!canProceed() || completeSetup.isPending}
                  className="border border-cyber-pink bg-cyber-pink font-mono text-white hover:bg-cyber-pink/90 hover:shadow-[0_0_16px_rgba(255,20,147,0.5)] disabled:opacity-40"
                >
                  {completeSetup.isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Setting up...
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      Launch Syntrix
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
