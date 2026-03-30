/** Access key management for the access gate middleware. */

const STORAGE_KEY = 'corvus-access-key';

export function getAccessKey(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

export function setAccessKey(key: string): void {
  localStorage.setItem(STORAGE_KEY, key);
}

export function clearAccessKey(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function getAuthHeaders(): Record<string, string> {
  const key = getAccessKey();
  if (key) {
    return { Authorization: `Bearer ${key}` };
  }
  return {};
}

/** Authenticated fetch wrapper — injects access key header automatically. */
export function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const headers = { ...getAuthHeaders(), ...(init?.headers || {}) };
  return fetch(url, { ...init, headers });
}

/** Check if the server requires an access key and if ours is valid. */
export async function checkAccess(): Promise<'open' | 'valid' | 'invalid'> {
  try {
    // Try an authenticated request to a non-exempt endpoint
    const res = await fetch('/neurons/stats', {
      headers: getAuthHeaders(),
    });
    if (res.ok) return getAccessKey() ? 'valid' : 'open';
    if (res.status === 401) return 'invalid';
    return 'open'; // other errors — assume open
  } catch {
    return 'open';
  }
}
