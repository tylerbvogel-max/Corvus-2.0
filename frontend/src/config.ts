/** Tenant configuration — fetched once from /tenant on app init. */

export interface TenantConfig {
  tenant_id: string;
  display_name: string;
  description: string;
}

let _cached: TenantConfig | null = null;

export async function fetchTenantConfig(): Promise<TenantConfig> {
  if (_cached) return _cached;
  try {
    const resp = await fetch('/tenant');
    if (resp.ok) {
      _cached = await resp.json();
      return _cached!;
    }
  } catch {
    // Fallback for dev/offline
  }
  _cached = {
    tenant_id: 'corvus-aero',
    display_name: 'Corvus Aero',
    description: 'Biomimetic neuron graph for aerospace defense prompt preparation.',
  };
  return _cached;
}

export function getTenantConfig(): TenantConfig | null {
  return _cached;
}
