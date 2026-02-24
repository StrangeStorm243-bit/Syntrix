const API_BASE = import.meta.env.VITE_API_URL || '';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getApiKey(): string {
  return localStorage.getItem('signalops_api_key') || '';
}

export function setApiKey(key: string): void {
  localStorage.setItem('signalops_api_key', key);
}

export function getStoredApiKey(): string {
  return getApiKey();
}

async function request<T>(
  method: string,
  path: string,
  params?: Record<string, string>,
  body?: unknown,
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
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

export function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  return request<T>('GET', path, params);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>('POST', path, undefined, body);
}
