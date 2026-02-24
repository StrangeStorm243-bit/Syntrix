import { useState } from 'react';
import { getStoredApiKey, setApiKey } from '../lib/api';

export default function Settings() {
  const [key, setKey] = useState(getStoredApiKey());
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setApiKey(key);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="max-w-md space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-400">API Key</label>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Enter your SignalOps API key"
            className="mt-1 w-full rounded border border-gray-600 bg-gray-800 px-3 py-2 text-white placeholder-gray-500"
          />
        </div>

        <button
          onClick={handleSave}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {saved ? 'Saved!' : 'Save'}
        </button>
      </div>
    </div>
  );
}
