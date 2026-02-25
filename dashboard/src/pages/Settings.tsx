import { useState } from 'react';
import { getStoredApiKey, setApiKey } from '../lib/api';
import { GlassCard } from '../components/cyber/GlassCard';
import { NeonInput } from '../components/cyber/NeonInput';
import { NeonButton } from '../components/cyber/NeonButton';
import { usePerformanceMode } from '../hooks/usePerformanceMode';

export default function Settings() {
  const [key, setKey] = useState(getStoredApiKey());
  const [saved, setSaved] = useState(false);
  const { performanceMode, toggle } = usePerformanceMode();

  function handleSave() {
    setApiKey(key);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-cyber-text">Settings</h1>

      <div className="max-w-lg space-y-6">
        {/* API Key */}
        <GlassCard>
          <h2 className="mb-4 text-sm font-medium text-cyber-text-dim">API Configuration</h2>
          <div className="space-y-4">
            <NeonInput
              label="API Key"
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Enter your Syntrix API key"
            />
            <NeonButton onClick={handleSave}>
              {saved ? 'Saved!' : 'Save'}
            </NeonButton>
          </div>
        </GlassCard>

        {/* Performance Mode */}
        <GlassCard>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-cyber-text">Performance Mode</h2>
              <p className="mt-1 text-xs text-cyber-text-dim">
                Disable 3D scenes and particles for better performance on low-end devices.
              </p>
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
    </div>
  );
}
