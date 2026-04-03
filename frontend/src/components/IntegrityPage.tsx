import { useState, useEffect, useCallback } from 'react';
import {
  fetchIntegrityDashboard,
  fetchIntegrityFindings,
  fetchIntegrityFindingDetail,
  resolveIntegrityFinding,
  dismissIntegrityFinding,
  bulkResolveIntegrityFindings,
  runHomeostasisScan,
  runDuplicatesScan,
  runConnectionsScan,
  runConflictsScan,
  runAgingScan,
  applyHomeostasisScan,
} from '../api';
import type {
  IntegrityDashboard,
  IntegrityFinding,
  IntegrityFindingDetail,
  IntegrityScanSummary,
  IntegrityScanResponse,
  IntegrityWeightDistribution,
} from '../types';

type Panel = 'dashboard' | 'scan' | 'findings';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#e74c3c',
  warning: '#f59e0b',
  info: '#3b82f6',
};

const STATUS_COLORS: Record<string, string> = {
  open: '#f59e0b',
  proposed: '#3b82f6',
  resolved: '#4caf50',
  dismissed: '#888',
};

const FINDING_TYPE_LABELS: Record<string, string> = {
  weight_inflation: 'Weight Imbalance',
  duplicate: 'Duplicate',
  missing_connection: 'Missing Connection',
  contradiction: 'Contradiction',
  stale_content: 'Stale Content',
};

const SCAN_TYPE_LABELS: Record<string, string> = {
  homeostasis: 'Homeostasis',
  duplicate_detection: 'Duplicate Detection',
  missing_connections: 'Missing Connections',
  conflict_detection: 'Conflict Detection',
  aging_review: 'Aging Review',
};

const RESOLUTION_OPTIONS: Record<string, Array<{ label: string; value: string }>> = {
  duplicate: [
    { label: 'Merge', value: 'merged' },
    { label: 'Differentiate', value: 'differentiated' },
  ],
  missing_connection: [
    { label: 'Link', value: 'linked' },
  ],
  contradiction: [
    { label: 'A Correct', value: 'a_correct' },
    { label: 'B Correct', value: 'b_correct' },
    { label: 'Add Context', value: 'context_added' },
  ],
  stale_content: [
    { label: 'Mark Reviewed', value: 'reviewed' },
    { label: 'Flag for Update', value: 'flagged' },
  ],
};

const selectStyle: React.CSSProperties = {
  background: 'var(--bg-input)', color: 'var(--text)', border: '1px solid var(--border)',
  borderRadius: 4, padding: '4px 8px', fontSize: '0.8rem',
};

const inputStyle: React.CSSProperties = {
  ...selectStyle, width: 80, boxSizing: 'border-box' as const,
};

const btnStyle: React.CSSProperties = {
  padding: '4px 12px', borderRadius: 4, border: '1px solid var(--border)',
  background: 'var(--bg-card)', color: 'var(--text)', cursor: 'pointer',
  fontSize: '0.8rem', fontWeight: 600,
};

function SeverityBadge({ severity }: { severity: string }) {
  const color = SEVERITY_COLORS[severity] || '#888';
  return (
    <span style={{
      display: 'inline-block', padding: '1px 6px', borderRadius: 4,
      fontSize: '0.7rem', fontWeight: 600,
      background: color + '22', color, border: `1px solid ${color}44`,
    }}>
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || '#888';
  return (
    <span style={{
      display: 'inline-block', padding: '1px 6px', borderRadius: 4,
      fontSize: '0.7rem', fontWeight: 600,
      background: color + '22', color, border: `1px solid ${color}44`,
    }}>
      {status}
    </span>
  );
}

// ── Dashboard Panel ──────────────────────────────────────────────

function DashboardPanel() {
  const [data, setData] = useState<IntegrityDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchIntegrityDashboard());
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div style={{ color: 'var(--text-dim)', padding: 16, fontSize: '0.85rem' }}>Loading dashboard...</div>;
  if (error) return <div style={{ color: '#e74c3c', padding: 16, fontSize: '0.85rem' }}>{error}</div>;
  if (!data) return null;

  const findingTypes = ['weight_inflation', 'duplicate', 'missing_connection', 'contradiction', 'stale_content'];
  const severities = ['critical', 'warning', 'info'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Open findings total */}
      <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
        <strong style={{ color: 'var(--text)', fontSize: '1.1rem' }}>{data.open_findings_total}</strong> open findings
      </div>

      {/* Finding type cards */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {findingTypes.map(t => (
          <div key={t} style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6,
            padding: '10px 14px', minWidth: 120, flex: '1 1 120px',
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: 4 }}>
              {FINDING_TYPE_LABELS[t] || t}
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text)' }}>
              {data.open_by_type[t] || 0}
            </div>
          </div>
        ))}
      </div>

      {/* Severity breakdown */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginRight: 4 }}>By severity:</span>
        {severities.map(s => {
          const count = data.open_by_severity[s] || 0;
          const color = SEVERITY_COLORS[s];
          return (
            <span key={s} style={{
              padding: '2px 8px', borderRadius: 10,
              background: color + '22', color, fontWeight: 600, fontSize: '0.75rem',
            }}>
              {s}: {count}
            </span>
          );
        })}
      </div>

      {/* Recent scans */}
      <div>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>Recent Scans</div>
        {data.recent_scans.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>No scans yet.</div>
        ) : (
          <table className="score-table" style={{ width: '100%', fontSize: '0.75rem' }}>
            <thead>
              <tr>
                <th>Type</th>
                <th>Scope</th>
                <th>Findings</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_scans.map((s: IntegrityScanSummary) => (
                <tr key={s.id}>
                  <td>{SCAN_TYPE_LABELS[s.scan_type] || s.scan_type}</td>
                  <td>{s.scope}</td>
                  <td>{s.findings_count}</td>
                  <td><StatusBadge status={s.status} /></td>
                  <td>{s.completed_at ? new Date(s.completed_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ── Scan Panel ───────────────────────────────────────────────────

interface ScanFormState {
  scope: string;
  [key: string]: string | number | boolean;
}

function ScanPanel() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, IntegrityScanResponse | null>>({});
  const [applyMsg, setApplyMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [homeo, setHomeo] = useState({ scope: 'global', scale_factor: 0.8, floor_threshold: 0.05 });
  const [dupes, setDupes] = useState({ scope: 'global', similarity_threshold: 0.92, max_pairs: 100, cross_department_only: false });
  const [conns, setConns] = useState({ scope: 'global', similarity_threshold: 0.65, max_suggestions: 50, exclude_same_parent: true });
  const [conflicts, setConflicts] = useState({ scope: 'global', sim_min: 0.60, sim_max: 0.85, batch_size: 5, max_pairs: 200 });
  const [aging, setAging] = useState({ scope: 'global', include_never_verified: true, min_invocations: 0 });

  const toggle = (key: string) => setExpanded(prev => prev === key ? null : key);

  const runScan = async (key: string, fn: () => Promise<IntegrityScanResponse>) => {
    setRunning(key);
    setError(null);
    setApplyMsg(null);
    try {
      const result = await fn();
      setResults(prev => ({ ...prev, [key]: result }));
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(null);
    }
  };

  const handleApply = async (scanId: number) => {
    setRunning('apply');
    setError(null);
    try {
      const result = await applyHomeostasisScan(scanId, 'admin');
      setApplyMsg(`Proposal #${result.proposal_id} created (${result.item_count} items). Review it in the Proposal Queue.`);
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(null);
    }
  };

  const accordionHeader = (key: string, label: string, description: string) => (
    <button
      onClick={() => toggle(key)}
      style={{
        width: '100%', textAlign: 'left', padding: '10px 12px',
        background: expanded === key ? 'var(--bg-active)' : 'var(--bg-card)',
        border: '1px solid var(--border)', borderRadius: expanded === key ? '6px 6px 0 0' : 6,
        color: 'var(--text)', cursor: 'pointer', display: 'flex', justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{label}</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 2 }}>{description}</div>
      </div>
      <span style={{ fontSize: '0.7rem' }}>{expanded === key ? '\u25BC' : '\u25B6'}</span>
    </button>
  );

  const formRow = (label: string, input: React.ReactNode) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', width: 140, flexShrink: 0 }}>{label}</label>
      {input}
    </div>
  );

  const renderDistribution = (label: string, dist: IntegrityWeightDistribution) => (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <table className="score-table" style={{ width: '100%', fontSize: '0.7rem' }}>
        <tbody>
          {(['count', 'mean', 'median', 'std', 'p10', 'p25', 'p75', 'p90', 'max'] as const).map(k => (
            <tr key={k}>
              <td style={{ fontWeight: 500, color: 'var(--text-dim)' }}>{k}</td>
              <td>{typeof dist[k] === 'number' ? (k === 'count' ? dist[k] : dist[k].toFixed(4)) : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const accordionBody = (content: React.ReactNode) => (
    <div style={{
      border: '1px solid var(--border)', borderTop: 'none',
      borderRadius: '0 0 6px 6px', padding: 12,
      display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      {content}
    </div>
  );

  const homeoResult = results['homeostasis'] as (IntegrityScanResponse & { before?: IntegrityWeightDistribution; after?: IntegrityWeightDistribution }) | null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {error && <div style={{ color: '#e74c3c', fontSize: '0.8rem', padding: '6px 0' }}>{error}</div>}

      {/* Homeostasis */}
      {accordionHeader('homeostasis', 'Synaptic Homeostasis', 'Multiplicative weight renormalization to prevent co-firing inflation')}
      {expanded === 'homeostasis' && accordionBody(
        <>
          {formRow('Scope', <input style={inputStyle} value={homeo.scope} onChange={e => setHomeo({ ...homeo, scope: e.target.value })} />)}
          {formRow('Scale Factor (0-1)', <input type="number" step="0.05" min="0.01" max="1" style={inputStyle} value={homeo.scale_factor} onChange={e => setHomeo({ ...homeo, scale_factor: parseFloat(e.target.value) || 0.8 })} />)}
          {formRow('Floor Threshold', <input type="number" step="0.01" min="0" style={inputStyle} value={homeo.floor_threshold} onChange={e => setHomeo({ ...homeo, floor_threshold: parseFloat(e.target.value) || 0 })} />)}
          <button style={btnStyle} disabled={running !== null} onClick={() => runScan('homeostasis', () => runHomeostasisScan(homeo))}>
            {running === 'homeostasis' ? 'Scanning...' : 'Run Scan'}
          </button>
          {homeoResult && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
              <div style={{ fontSize: '0.8rem', marginBottom: 8 }}>
                <StatusBadge status={homeoResult.status} /> {homeoResult.findings_count} finding(s)
              </div>
              {homeoResult.before && homeoResult.after && (
                <div style={{ display: 'flex', gap: 16 }}>
                  {renderDistribution('Before', homeoResult.before)}
                  {renderDistribution('After', homeoResult.after)}
                </div>
              )}
              {homeoResult.findings_count > 0 && (
                <div style={{ marginTop: 8 }}>
                  <button
                    style={{ ...btnStyle, background: 'var(--accent)', color: '#fff', border: 'none' }}
                    disabled={running === 'apply'}
                    onClick={() => handleApply(homeoResult.id)}
                  >
                    {running === 'apply' ? 'Creating Proposal...' : 'Apply Rescaling'}
                  </button>
                  {applyMsg && <div style={{ fontSize: '0.75rem', color: '#4caf50', marginTop: 6 }}>{applyMsg}</div>}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Duplicates */}
      {accordionHeader('duplicates', 'Pattern Separation (Duplicates)', 'Near-duplicate neuron detection via cosine similarity')}
      {expanded === 'duplicates' && accordionBody(
        <>
          {formRow('Scope', <input style={inputStyle} value={dupes.scope} onChange={e => setDupes({ ...dupes, scope: e.target.value })} />)}
          {formRow('Similarity Threshold', <input type="number" step="0.01" min="0.5" max="1" style={inputStyle} value={dupes.similarity_threshold} onChange={e => setDupes({ ...dupes, similarity_threshold: parseFloat(e.target.value) || 0.92 })} />)}
          {formRow('Max Pairs', <input type="number" min="1" max="500" style={inputStyle} value={dupes.max_pairs} onChange={e => setDupes({ ...dupes, max_pairs: parseInt(e.target.value) || 100 })} />)}
          {formRow('Cross-Dept Only', <input type="checkbox" checked={dupes.cross_department_only} onChange={e => setDupes({ ...dupes, cross_department_only: e.target.checked })} />)}
          <button style={btnStyle} disabled={running !== null} onClick={() => runScan('duplicates', () => runDuplicatesScan(dupes))}>
            {running === 'duplicates' ? 'Scanning...' : 'Run Scan'}
          </button>
          {results['duplicates'] && <ScanResultSummary result={results['duplicates']} />}
        </>
      )}

      {/* Connections */}
      {accordionHeader('connections', 'Pattern Completion (Connections)', 'Find missing semantic connections between neurons')}
      {expanded === 'connections' && accordionBody(
        <>
          {formRow('Scope', <input style={inputStyle} value={conns.scope} onChange={e => setConns({ ...conns, scope: e.target.value })} />)}
          {formRow('Similarity Threshold', <input type="number" step="0.05" min="0.3" max="1" style={inputStyle} value={conns.similarity_threshold} onChange={e => setConns({ ...conns, similarity_threshold: parseFloat(e.target.value) || 0.65 })} />)}
          {formRow('Max Suggestions', <input type="number" min="1" max="500" style={inputStyle} value={conns.max_suggestions} onChange={e => setConns({ ...conns, max_suggestions: parseInt(e.target.value) || 50 })} />)}
          {formRow('Exclude Same Parent', <input type="checkbox" checked={conns.exclude_same_parent} onChange={e => setConns({ ...conns, exclude_same_parent: e.target.checked })} />)}
          <button style={btnStyle} disabled={running !== null} onClick={() => runScan('connections', () => runConnectionsScan(conns))}>
            {running === 'connections' ? 'Scanning...' : 'Run Scan'}
          </button>
          {results['connections'] && <ScanResultSummary result={results['connections']} />}
        </>
      )}

      {/* Conflicts */}
      {accordionHeader('conflicts', 'Conflict Monitor', 'Contradiction detection via embedding prefilter + LLM classification')}
      {expanded === 'conflicts' && accordionBody(
        <>
          {formRow('Scope', <input style={inputStyle} value={conflicts.scope} onChange={e => setConflicts({ ...conflicts, scope: e.target.value })} />)}
          {formRow('Similarity Min', <input type="number" step="0.05" min="0" max="1" style={inputStyle} value={conflicts.sim_min} onChange={e => setConflicts({ ...conflicts, sim_min: parseFloat(e.target.value) || 0.6 })} />)}
          {formRow('Similarity Max', <input type="number" step="0.05" min="0" max="1" style={inputStyle} value={conflicts.sim_max} onChange={e => setConflicts({ ...conflicts, sim_max: parseFloat(e.target.value) || 0.85 })} />)}
          {formRow('Batch Size', <input type="number" min="1" max="20" style={inputStyle} value={conflicts.batch_size} onChange={e => setConflicts({ ...conflicts, batch_size: parseInt(e.target.value) || 5 })} />)}
          {formRow('Max Pairs', <input type="number" min="1" max="1000" style={inputStyle} value={conflicts.max_pairs} onChange={e => setConflicts({ ...conflicts, max_pairs: parseInt(e.target.value) || 200 })} />)}
          <div style={{ fontSize: '0.7rem', color: '#f59e0b', fontStyle: 'italic' }}>
            Note: This scan calls the LLM and has cost implications.
          </div>
          <button style={btnStyle} disabled={running !== null} onClick={() => runScan('conflicts', () => runConflictsScan(conflicts))}>
            {running === 'conflicts' ? 'Scanning...' : 'Run Scan'}
          </button>
          {results['conflicts'] && <ScanResultSummary result={results['conflicts']} />}
        </>
      )}

      {/* Aging */}
      {accordionHeader('aging', 'Age-Based Review', 'Surface stale neurons by source type and usage patterns')}
      {expanded === 'aging' && accordionBody(
        <>
          {formRow('Scope', <input style={inputStyle} value={aging.scope} onChange={e => setAging({ ...aging, scope: e.target.value })} />)}
          {formRow('Include Never Verified', <input type="checkbox" checked={aging.include_never_verified} onChange={e => setAging({ ...aging, include_never_verified: e.target.checked })} />)}
          {formRow('Min Invocations', <input type="number" min="0" style={inputStyle} value={aging.min_invocations} onChange={e => setAging({ ...aging, min_invocations: parseInt(e.target.value) || 0 })} />)}
          <button style={btnStyle} disabled={running !== null} onClick={() => runScan('aging', () => runAgingScan(aging))}>
            {running === 'aging' ? 'Scanning...' : 'Run Scan'}
          </button>
          {results['aging'] && <ScanResultSummary result={results['aging']} />}
        </>
      )}
    </div>
  );
}

function ScanResultSummary({ result }: { result: IntegrityScanResponse }) {
  return (
    <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10, fontSize: '0.8rem' }}>
      <StatusBadge status={result.status} /> {result.findings_count} finding(s) &middot; Scope: {result.scope}
      {result.completed_at && (
        <span style={{ color: 'var(--text-dim)', marginLeft: 8 }}>
          {new Date(result.completed_at).toLocaleString()}
        </span>
      )}
    </div>
  );
}

// ── Findings Queue Panel ─────────────────────────────────────────

function FindingsPanel() {
  const [findings, setFindings] = useState<IntegrityFinding[]>([]);
  const [selected, setSelected] = useState<IntegrityFindingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [queueCollapsed, setQueueCollapsed] = useState(false);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('open');
  const [severityFilter, setSeverityFilter] = useState<string>('');

  // Reviewer
  const [reviewer, setReviewer] = useState('');
  const [notes, setNotes] = useState('');

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkResolution, setBulkResolution] = useState('dismissed');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const f = await fetchIntegrityFindings({
        finding_type: typeFilter || undefined,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      });
      setFindings(f);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [typeFilter, statusFilter, severityFilter]);

  useEffect(() => { load(); }, [load]);

  const selectFinding = async (id: number) => {
    try {
      const detail = await fetchIntegrityFindingDetail(id);
      setSelected(detail);
      setNotes('');
    } catch (e) {
      setError(String(e));
    }
  };

  const handleResolve = async (resolution: string) => {
    if (!selected || !reviewer.trim()) return;
    setActionLoading(true);
    try {
      await resolveIntegrityFinding(selected.id, resolution, reviewer.trim(), notes);
      setSelected(null);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDismiss = async () => {
    if (!selected || !reviewer.trim()) return;
    setActionLoading(true);
    try {
      await dismissIntegrityFinding(selected.id, reviewer.trim(), notes);
      setSelected(null);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkResolve = async () => {
    if (selectedIds.size === 0 || !reviewer.trim()) return;
    setActionLoading(true);
    try {
      await bulkResolveIntegrityFindings(Array.from(selectedIds), bulkResolution, reviewer.trim(), notes);
      setSelectedIds(new Set());
      setSelected(null);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setActionLoading(false);
    }
  };

  const toggleBulkId = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const resolutionOptions = selected ? (RESOLUTION_OPTIONS[selected.finding_type] || []) : [];

  return (
    <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - 180px)' }}>
      {/* Left Panel */}
      <div style={{
        width: queueCollapsed ? 40 : 360, flexShrink: 0,
        display: 'flex', flexDirection: 'column',
        borderRight: '1px solid var(--border)', transition: 'width 0.2s ease', overflow: 'hidden',
      }}>
        <button
          onClick={() => setQueueCollapsed(!queueCollapsed)}
          style={{
            background: 'none', border: 'none', color: 'var(--text)',
            cursor: 'pointer', padding: '8px 10px', fontSize: '0.85rem',
            display: 'flex', alignItems: 'center', gap: 6,
            borderBottom: '1px solid var(--border)',
          }}
        >
          <span style={{ fontSize: '0.7rem' }}>{queueCollapsed ? '\u25B6' : '\u25C0'}</span>
          {!queueCollapsed && <span style={{ fontWeight: 600 }}>Findings ({findings.length})</span>}
        </button>

        {!queueCollapsed && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '8px 8px', flex: 1, overflow: 'hidden' }}>
            {/* Filters */}
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
                <option value="">All Types</option>
                <option value="weight_inflation">Weight Imbalance</option>
                <option value="duplicate">Duplicate</option>
                <option value="missing_connection">Missing Connection</option>
                <option value="contradiction">Contradiction</option>
                <option value="stale_content">Stale Content</option>
              </select>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
                <option value="">All Status</option>
                <option value="open">Open</option>
                <option value="proposed">Proposed</option>
                <option value="resolved">Resolved</option>
                <option value="dismissed">Dismissed</option>
              </select>
              <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} style={{ ...selectStyle, flex: 1 }}>
                <option value="">All Severity</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
            </div>

            {/* Bulk actions */}
            {selectedIds.size > 0 && (
              <div style={{
                display: 'flex', gap: 4, alignItems: 'center', padding: '4px 0',
                borderBottom: '1px solid var(--border)', fontSize: '0.75rem',
              }}>
                <span style={{ color: 'var(--text-dim)' }}>{selectedIds.size} selected</span>
                <select value={bulkResolution} onChange={e => setBulkResolution(e.target.value)} style={selectStyle}>
                  <option value="dismissed">Dismiss</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="merged">Merged</option>
                  <option value="linked">Linked</option>
                </select>
                <button style={btnStyle} disabled={actionLoading || !reviewer.trim()} onClick={handleBulkResolve}>
                  Bulk Apply
                </button>
              </div>
            )}

            {/* List */}
            <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
              {loading && <div style={{ color: 'var(--text-dim)', padding: 8, fontSize: '0.8rem' }}>Loading...</div>}
              {error && <div style={{ color: '#e74c3c', padding: 8, fontSize: '0.8rem' }}>{error}</div>}
              {!loading && findings.length === 0 && (
                <div style={{ color: 'var(--text-dim)', padding: 8, fontSize: '0.8rem' }}>No findings found.</div>
              )}
              {findings.map(f => (
                <div
                  key={f.id}
                  style={{
                    padding: '6px 8px', borderRadius: 6, cursor: 'pointer',
                    background: selected?.id === f.id ? 'var(--bg-active)' : 'var(--bg-card)',
                    border: `1px solid ${selected?.id === f.id ? 'var(--accent)' : 'var(--border)'}`,
                    display: 'flex', gap: 6, alignItems: 'flex-start',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(f.id)}
                    onChange={() => toggleBulkId(f.id)}
                    style={{ marginTop: 3, flexShrink: 0 }}
                  />
                  <div style={{ flex: 1 }} onClick={() => selectFinding(f.id)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 4 }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                        {FINDING_TYPE_LABELS[f.finding_type] || f.finding_type}
                      </span>
                      <SeverityBadge severity={f.severity} />
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: 2, lineHeight: 1.3 }}>
                      {f.description.length > 100 ? f.description.slice(0, 100) + '...' : f.description}
                    </div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 3, fontSize: '0.65rem', color: 'var(--text-dim)' }}>
                      <span>Score: {f.priority_score.toFixed(2)}</span>
                      <StatusBadge status={f.status} />
                      {f.created_at && <span>{new Date(f.created_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right Panel — Detail */}
      <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
        {!selected ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem', paddingTop: 32, textAlign: 'center' }}>
            Select a finding to view details
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Header */}
            <div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Finding #{selected.id}</span>
                <SeverityBadge severity={selected.severity} />
                <StatusBadge status={selected.status} />
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Type: {FINDING_TYPE_LABELS[selected.finding_type] || selected.finding_type}
                &nbsp;&middot;&nbsp;Priority: {selected.priority_score.toFixed(2)}
                {selected.created_at && <>&nbsp;&middot;&nbsp;{new Date(selected.created_at).toLocaleString()}</>}
              </div>
            </div>

            {/* Description */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: 4 }}>Description</div>
              <div style={{ fontSize: '0.8rem', lineHeight: 1.5 }}>{selected.description}</div>
            </div>

            {/* Detail JSON */}
            {selected.detail && Object.keys(selected.detail).length > 0 && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: 4 }}>Detail</div>
                <pre style={{
                  fontSize: '0.7rem', background: 'var(--bg-input)', padding: 8, borderRadius: 4,
                  overflow: 'auto', maxHeight: 200, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                }}>
                  {JSON.stringify(selected.detail, null, 2)}
                </pre>
              </div>
            )}

            {/* Neurons */}
            {Object.keys(selected.neurons).length > 0 && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: 8 }}>Referenced Neurons</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {Object.values(selected.neurons).map(n => (
                    <div key={n.id} style={{
                      background: 'var(--bg-card)', border: '1px solid var(--border)',
                      borderRadius: 6, padding: 10,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>#{n.id} {n.label}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                          L{n.layer} &middot; {n.department || 'no dept'} &middot; {n.invocations} invocations
                        </span>
                      </div>
                      {n.summary && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: 4 }}>{n.summary}</div>
                      )}
                      {n.content && (
                        <pre style={{
                          fontSize: '0.7rem', background: 'var(--bg-input)', padding: 8, borderRadius: 4,
                          overflow: 'auto', maxHeight: 200, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                          margin: 0,
                        }}>
                          {n.content}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {(selected.status === 'open' || selected.status === 'proposed') && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: 8 }}>Actions</div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', width: 60 }}>Reviewer</label>
                    <input
                      style={{ ...selectStyle, flex: 1 }}
                      value={reviewer}
                      onChange={e => setReviewer(e.target.value)}
                      placeholder="Your name"
                    />
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', width: 60, paddingTop: 4 }}>Notes</label>
                    <textarea
                      style={{ ...selectStyle, flex: 1, minHeight: 40, resize: 'vertical', fontFamily: 'inherit' }}
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      placeholder="Optional notes..."
                    />
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {resolutionOptions.map(opt => (
                      <button
                        key={opt.value}
                        style={{ ...btnStyle, background: 'var(--accent)', color: '#fff', border: 'none' }}
                        disabled={actionLoading || !reviewer.trim()}
                        onClick={() => handleResolve(opt.value)}
                      >
                        {opt.label}
                      </button>
                    ))}
                    <button
                      style={btnStyle}
                      disabled={actionLoading || !reviewer.trim()}
                      onClick={handleDismiss}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Resolution info for already-resolved findings */}
            {selected.status === 'resolved' && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10, fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-dim)' }}>Resolved as </span>
                <strong>{selected.resolution}</strong>
                {selected.resolved_by && <span style={{ color: 'var(--text-dim)' }}> by {selected.resolved_by}</span>}
                {selected.resolved_at && <span style={{ color: 'var(--text-dim)' }}> on {new Date(selected.resolved_at).toLocaleString()}</span>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────

export default function IntegrityPage() {
  const [panel, setPanel] = useState<Panel>('dashboard');

  const tabBtn = (key: Panel, label: string) => (
    <button
      key={key}
      onClick={() => setPanel(key)}
      style={{
        background: 'none', border: 'none', color: panel === key ? 'var(--accent)' : 'var(--text-dim)',
        cursor: 'pointer', padding: '8px 16px', fontSize: '0.85rem', fontWeight: 600,
        borderBottom: panel === key ? '2px solid var(--accent)' : '2px solid transparent',
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 12 }}>
        {tabBtn('dashboard', 'Dashboard')}
        {tabBtn('scan', 'Scan')}
        {tabBtn('findings', 'Findings Queue')}
      </div>

      {/* Panel content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 4px' }}>
        {panel === 'dashboard' && <DashboardPanel />}
        {panel === 'scan' && <ScanPanel />}
        {panel === 'findings' && <FindingsPanel />}
      </div>
    </div>
  );
}
