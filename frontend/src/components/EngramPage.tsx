import { useEffect, useState } from 'react';

interface EngramSummary {
  id: number;
  label: string;
  summary: string | null;
  cfr_title: number;
  cfr_part: string;
  cfr_section: string | null;
  source_api: string;
  authority_level: string;
  issuing_body: string | null;
  invocations: number;
  avg_utility: number;
  cached: boolean;
  cached_at: string | null;
  cached_token_count: number | null;
  has_embedding: boolean;
  is_active: boolean;
}

interface EngramStats {
  total: number;
  active: number;
  cached: number;
  embedded: number;
}

interface ResolveResult {
  engram_id: number;
  cfr_ref: string;
  token_count: number;
  text_preview: string;
  cached_at: string;
}

function cfr_ref(e: EngramSummary): string {
  const section = e.cfr_section ? `.${e.cfr_section}` : '';
  return `${e.cfr_title} CFR ${e.cfr_part}${section}`;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: ok ? 'var(--green, #22c55e)' : 'var(--text-dim, #666)',
        marginRight: 6,
      }}
    />
  );
}

export default function EngramPage() {
  const [engrams, setEngrams] = useState<EngramSummary[]>([]);
  const [stats, setStats] = useState<EngramStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<number | null>(null);
  const [resolveResult, setResolveResult] = useState<ResolveResult | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detailCache, setDetailCache] = useState<Record<number, { content: string | null }>>({});

  useEffect(() => {
    Promise.all([
      fetch('/engrams/').then(r => r.json()),
      fetch('/engrams/stats/summary').then(r => r.json()),
    ]).then(([e, s]) => {
      setEngrams(e);
      setStats(s);
    }).finally(() => setLoading(false));
  }, []);

  async function handleResolve(id: number) {
    setResolving(id);
    setResolveResult(null);
    try {
      const resp = await fetch(`/engrams/${id}/resolve`, { method: 'POST' });
      const data = await resp.json();
      if (data.error) {
        setResolveResult(null);
        alert(`Resolve failed: ${data.error}`);
      } else {
        setResolveResult(data);
        // Refresh list to show updated cache status
        const updated = await fetch('/engrams/').then(r => r.json());
        setEngrams(updated);
      }
    } finally {
      setResolving(null);
    }
  }

  if (loading) {
    return <div style={{ padding: 24, color: 'var(--text-dim)' }}>Loading engrams...</div>;
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1100 }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ color: 'var(--text)', fontSize: 20, fontWeight: 700, margin: '0 0 6px' }}>
          Engrams
        </h2>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, margin: 0 }}>
          Retrieval indices for external regulatory sources. Engrams participate in neuron scoring
          but fetch authoritative text live from the eCFR API at query time.
        </p>
      </div>

      {/* Stats bar */}
      {stats && (
        <div style={{
          display: 'flex', gap: 16, marginBottom: 20,
          padding: '12px 16px', borderRadius: 8,
          background: 'var(--bg-card)', border: '1px solid var(--border)',
        }}>
          {[
            { label: 'Total', value: stats.total, color: 'var(--text)' },
            { label: 'Active', value: stats.active, color: 'var(--green, #22c55e)' },
            { label: 'Embedded', value: stats.embedded, color: 'var(--blue, #4a9eff)' },
            { label: 'Cached', value: stats.cached, color: 'var(--amber, #f59e0b)' },
          ].map(s => (
            <div key={s.label} style={{ textAlign: 'center', minWidth: 70 }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: s.color, fontFamily: 'monospace' }}>
                {s.value}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: 1 }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Engram table */}
      <div style={{
        borderRadius: 8, overflow: 'hidden',
        border: '1px solid var(--border)', background: 'var(--bg-card)',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: 'var(--bg-input)' }}>
              <th style={thStyle}>ID</th>
              <th style={{ ...thStyle, textAlign: 'left' }}>CFR Reference</th>
              <th style={{ ...thStyle, textAlign: 'left' }}>Label</th>
              <th style={thStyle}>Embed</th>
              <th style={thStyle}>Cache</th>
              <th style={thStyle}>Tokens</th>
              <th style={thStyle}>Fires</th>
              <th style={thStyle}>Utility</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {engrams.map(e => (
              <EngramRow
                key={e.id}
                engram={e}
                expanded={expanded === e.id}
                onToggle={() => {
                  const next = expanded === e.id ? null : e.id;
                  setExpanded(next);
                  if (next !== null && !detailCache[e.id]) {
                    fetch(`/engrams/${e.id}`).then(r => r.json()).then(d => {
                      setDetailCache(prev => ({ ...prev, [e.id]: { content: d.content } }));
                    });
                  }
                }}
                onResolve={() => handleResolve(e.id)}
                resolving={resolving === e.id}
                content={detailCache[e.id]?.content ?? null}
              />
            ))}
            {engrams.length === 0 && (
              <tr>
                <td colSpan={9} style={{ padding: 24, textAlign: 'center', color: 'var(--text-dim)' }}>
                  No engrams seeded. Check tenant engram_seeds.py configuration.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Resolve result panel */}
      {resolveResult && (
        <div style={{
          marginTop: 16, padding: '16px 20px', borderRadius: 8,
          background: 'var(--bg-card)', border: '1px solid var(--green, #22c55e)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ color: 'var(--green, #22c55e)', fontWeight: 700, fontSize: 13 }}>
              Resolved: {resolveResult.cfr_ref}
            </span>
            <span style={{ color: 'var(--text-dim)', fontSize: 11, fontFamily: 'monospace' }}>
              {resolveResult.token_count.toLocaleString()} tokens | cached {resolveResult.cached_at}
            </span>
          </div>
          <pre style={{
            color: 'var(--text-dim)', fontSize: 11, lineHeight: 1.6,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 300, overflow: 'auto',
            background: 'var(--bg-input)', padding: 12, borderRadius: 6,
            margin: 0,
          }}>
            {resolveResult.text_preview}
          </pre>
          <button
            onClick={() => setResolveResult(null)}
            style={{
              marginTop: 8, padding: '4px 12px', fontSize: 11,
              background: 'none', border: '1px solid var(--border)',
              borderRadius: 4, color: 'var(--text-dim)', cursor: 'pointer',
            }}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: '10px 12px',
  color: 'var(--text-dim)',
  fontWeight: 600,
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
  textAlign: 'center',
};

function EngramRow({
  engram: e, expanded, onToggle, onResolve, resolving, content,
}: {
  engram: EngramSummary;
  expanded: boolean;
  onToggle: () => void;
  onResolve: () => void;
  resolving: boolean;
  content: string | null;
}) {
  const ref = cfr_ref(e);

  return (
    <>
      <tr
        style={{ borderTop: '1px solid var(--border)', cursor: 'pointer' }}
        onClick={onToggle}
      >
        <td style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'monospace', fontSize: 11 }}>
          {e.id}
        </td>
        <td style={{ padding: '8px 12px' }}>
          <span style={{
            display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11,
            fontFamily: 'monospace', fontWeight: 600,
            background: 'var(--accent, #c87533)' + '20',
            color: 'var(--accent, #c87533)',
          }}>
            {ref}
          </span>
        </td>
        <td style={{ padding: '8px 12px', color: 'var(--text)', fontSize: 12, maxWidth: 300 }}>
          {e.label.replace(/^\d+ CFR [\d.]+: /, '')}
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center' }}>
          <StatusDot ok={e.has_embedding} />
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center' }}>
          <StatusDot ok={e.cached} />
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'monospace', fontSize: 11 }}>
          {e.cached_token_count != null ? e.cached_token_count.toLocaleString() : '—'}
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'monospace', fontSize: 11 }}>
          {e.invocations}
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-dim)', fontFamily: 'monospace', fontSize: 11 }}>
          {e.avg_utility.toFixed(2)}
        </td>
        <td style={{ padding: '8px 12px', textAlign: 'center' }}>
          <button
            onClick={(ev) => { ev.stopPropagation(); onResolve(); }}
            disabled={resolving}
            style={{
              padding: '3px 10px', fontSize: 10, borderRadius: 4,
              background: resolving ? 'var(--bg-input)' : 'var(--accent, #c87533)' + '20',
              border: '1px solid var(--accent, #c87533)' + '40',
              color: 'var(--accent, #c87533)',
              cursor: resolving ? 'wait' : 'pointer',
              fontWeight: 600,
            }}
          >
            {resolving ? 'Fetching...' : 'Resolve'}
          </button>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={9} style={{ padding: '8px 20px 16px', background: 'var(--bg-input)' }}>
            <div style={{ fontSize: 11, marginBottom: 10 }}>
              <span style={{ color: 'var(--text-dim)' }}>Summary: </span>
              <span style={{ color: 'var(--text)' }}>{e.summary || '—'}</span>
            </div>
            <div style={{
              marginBottom: 10, padding: '8px 12px', borderRadius: 6,
              background: 'var(--bg-card)', border: '1px solid var(--accent, #c87533)30',
            }}>
              <div style={{ color: 'var(--accent, #c87533)', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
                Retrieval Cues (content)
              </div>
              <div style={{ color: 'var(--text)', fontSize: 11, fontFamily: 'monospace', lineHeight: 1.6 }}>
                {content ?? 'loading...'}
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 24px', fontSize: 11 }}>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Issuing Body: </span>
                <span style={{ color: 'var(--text)' }}>{e.issuing_body || '—'}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Authority: </span>
                <span style={{ color: 'var(--text)' }}>{e.authority_level}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Source API: </span>
                <span style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{e.source_api}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)' }}>Cached At: </span>
                <span style={{ color: 'var(--text)', fontFamily: 'monospace' }}>{e.cached_at || 'not cached'}</span>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
