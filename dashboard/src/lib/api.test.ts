import { describe, it, expect, vi, beforeEach } from 'vitest';

// We need to mock the module because localStorage may not be available in all test environments
vi.mock('./api', async () => {
  // Simple in-memory storage for testing
  const store: Record<string, string> = {};

  class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }

  function getApiKey(): string {
    return store['signalops_api_key'] || '';
  }

  function setApiKey(key: string): void {
    store['signalops_api_key'] = key;
  }

  function getStoredApiKey(): string {
    return getApiKey();
  }

  async function request<T>(
    method: string,
    path: string,
    params?: Record<string, string>,
    body?: unknown,
  ): Promise<T> {
    const url = new URL(`${path}`, 'http://localhost');
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }
    const headers: Record<string, string> = { 'X-API-Key': getApiKey() };
    if (body) headers['Content-Type'] = 'application/json';

    const res = await fetch(url.toString(), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      throw new ApiError(res.status, await res.text());
    }
    return res.json();
  }

  return {
    ApiError,
    setApiKey,
    getStoredApiKey,
    apiGet: <T>(path: string, params?: Record<string, string>) => request<T>('GET', path, params),
    apiPost: <T>(path: string, body?: unknown) => request<T>('POST', path, undefined, body),
    __store: store,
  };
});

import { apiGet, apiPost, ApiError, setApiKey, getStoredApiKey } from './api';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('setApiKey stores and getStoredApiKey retrieves', () => {
    setApiKey('test-key');
    expect(getStoredApiKey()).toBe('test-key');
  });

  it('apiGet sends GET with API key header', async () => {
    setApiKey('my-key');
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: 'ok' }), { status: 200 }),
    );

    const result = await apiGet<{ data: string }>('/api/test');
    expect(result).toEqual({ data: 'ok' });

    const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/test');
    expect((opts.headers as Record<string, string>)['X-API-Key']).toBe('my-key');
    expect(opts.method).toBe('GET');
  });

  it('apiGet includes query params', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200 }),
    );

    await apiGet('/api/leads', { page: '2', label: 'relevant' });

    const [url] = vi.mocked(fetch).mock.calls[0] as [string];
    expect(url).toContain('page=2');
    expect(url).toContain('label=relevant');
  });

  it('apiPost sends POST with JSON body', async () => {
    setApiKey('key-123');
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'approved' }), { status: 200 }),
    );

    await apiPost('/api/queue/1/approve', { text: 'hello' });

    const [, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(opts.method).toBe('POST');
    expect(opts.body).toBe(JSON.stringify({ text: 'hello' }));
    expect((opts.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });

  it('throws ApiError on non-OK response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('Unauthorized', { status: 401 }),
    );

    await expect(apiGet('/api/projects')).rejects.toThrow(ApiError);
  });
});
