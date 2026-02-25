import { useSyncExternalStore, useCallback } from 'react';

const STORAGE_KEY = 'syntrix-performance-mode';

const listeners = new Set<() => void>();

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function getSnapshot(): boolean {
  return localStorage.getItem(STORAGE_KEY) === 'true';
}

function getServerSnapshot(): boolean {
  return false;
}

function notify() {
  for (const cb of listeners) cb();
}

/**
 * Global performance mode toggle.
 * When enabled, 3D scenes and particles are disabled for low-end devices.
 * Uses useSyncExternalStore for tear-free reads across components.
 */
export function usePerformanceMode() {
  const enabled = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = useCallback(() => {
    const next = !getSnapshot();
    localStorage.setItem(STORAGE_KEY, String(next));
    notify();
  }, []);

  const setEnabled = useCallback((value: boolean) => {
    localStorage.setItem(STORAGE_KEY, String(value));
    notify();
  }, []);

  return { performanceMode: enabled, toggle, setEnabled } as const;
}
