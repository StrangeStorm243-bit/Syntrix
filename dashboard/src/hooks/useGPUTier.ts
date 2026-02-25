import { useState, useEffect } from 'react';

type GPUTier = 'high' | 'medium' | 'low';

interface GPUTierResult {
  tier: GPUTier;
  renderer: string;
}

const SESSION_KEY = 'gpu-tier';

function detectGPUTier(): GPUTierResult {
  try {
    const canvas = document.createElement('canvas');
    const gl =
      (canvas.getContext('webgl2') as WebGL2RenderingContext | null) ??
      (canvas.getContext('webgl') as WebGLRenderingContext | null);

    if (!gl) {
      return { tier: 'low', renderer: 'no-webgl' };
    }

    const isWebGL2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;

    if (!isWebGL2) {
      return { tier: 'low', renderer: 'webgl1-only' };
    }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');

    if (!debugInfo) {
      return { tier: 'low', renderer: 'unknown' };
    }

    const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) as string;

    const HIGH_KEYWORDS = ['NVIDIA', 'AMD', 'Radeon', 'GeForce', 'Apple'];
    const MEDIUM_KEYWORDS = ['Intel UHD', 'Intel Iris', 'Intel HD', 'Intel(R)'];

    const upper = renderer.toUpperCase();

    if (HIGH_KEYWORDS.some((kw) => upper.includes(kw.toUpperCase()))) {
      return { tier: 'high', renderer };
    }

    if (MEDIUM_KEYWORDS.some((kw) => upper.includes(kw.toUpperCase()))) {
      return { tier: 'medium', renderer };
    }

    return { tier: 'low', renderer };
  } catch {
    return { tier: 'low', renderer: 'error' };
  }
}

export function useGPUTier(): GPUTierResult {
  const [result, setResult] = useState<GPUTierResult>({ tier: 'low', renderer: '' });

  useEffect(() => {
    const cached = sessionStorage.getItem(SESSION_KEY);

    if (cached) {
      try {
        const parsed = JSON.parse(cached) as GPUTierResult;
        setResult(parsed);
        return;
      } catch {
        // Cache corrupt — fall through to detection
      }
    }

    const detected = detectGPUTier();
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(detected));
    setResult(detected);
  }, []);

  return result;
}
