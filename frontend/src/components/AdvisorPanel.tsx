import { useState, useEffect, useCallback, useRef } from 'react';
import type { ScreenCaptureState } from '../types/screenCapture';
import ScreenPreview from './ScreenPreview';

const CORVUS_API = '/corvus';

interface AdvisoryCitation {
  id: number;
  label: string;
  department: string | null;
  source_type: string;
  citation: string | null;
  source_url: string | null;
  score: number;
  content_preview: string;
}

interface Advisory {
  id: number;
  timestamp: string;
  trigger_context: string;
  guidance: string;
  top_score: number;
  citations: AdvisoryCitation[];
  intent: string | null;
  departments: string[];
  app_id: string | null;
  dismissed: boolean;
  cost_usd: number;
  created_at: string | null;
}

interface AdvisorSettings {
  enabled: boolean;
  threshold: number;
}

interface CaptureStatus {
  status: string;
  captures_stored: number;
  current_tokens: number;
  interpretation_mode: string;
  active_session_id: number | null;
}

interface Props {
  open: boolean;
  onClose: () => void;
  screenCapture: ScreenCaptureState;
}

export default function AdvisorPanel({ open, onClose, screenCapture }: Props) {
  const [settings, setSettings] = useState<AdvisorSettings>({ enabled: false, threshold: 0.5 });
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [capture, setCapture] = useState<CaptureStatus | null>(null);
  const [backendOk, setBackendOk] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const fetchSettings = useCallback(async () => {
    try {
      const r = await fetch(`${CORVUS_API}/settings/advisor`);
      if (r.ok) setSettings(await r.json());
    } catch {}
  }, []);

  const fetchAdvisories = useCallback(async () => {
    try {
      const r = await fetch(`${CORVUS_API}/advisories?limit=20`);
      if (r.ok) setAdvisories(await r.json());
    } catch {}
  }, []);

  const fetchCapture = useCallback(async () => {
    try {
      const r = await fetch(`${CORVUS_API}/status`);
      if (r.ok) {
        setCapture(await r.json());
        setBackendOk(true);
      } else {
        setBackendOk(false);
      }
    } catch {
      setBackendOk(false);
    }
  }, []);

  // Fetch on open
  useEffect(() => {
    if (!open) return;
    fetchSettings();
    fetchAdvisories();
    fetchCapture();
  }, [open]);

  // Poll when open
  useEffect(() => {
    if (!open) return;
    pollRef.current = setInterval(() => {
      fetchCapture();
      if (settings.enabled) fetchAdvisories();
    }, 5000);
    return () => clearInterval(pollRef.current);
  }, [open, settings.enabled]);

  async function updateSetting(key: string, value: string | boolean) {
    const fd = new FormData();
    fd.append(key, String(value));
    await fetch(`${CORVUS_API}/settings/advisor`, { method: 'POST', body: fd });
    fetchSettings();
  }

  async function dismiss(id: number) {
    await fetch(`${CORVUS_API}/advisories/${id}/dismiss`, { method: 'POST' });
    setAdvisories(prev => prev.filter(a => a.id !== id));
  }

  if (!open) return null;

  const capturing = screenCapture.isCapturing || (backendOk && capture && capture.captures_stored > 0);
  const buffered = capture?.current_tokens ?? 0;

  return (
    <>
      <div
        style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 999,
        }}
        onClick={onClose}
      />
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: 420,
        background: 'var(--bg-card, #1a1a2e)', borderLeft: '1px solid var(--border, #333)',
        zIndex: 1000, display: 'flex', flexDirection: 'column',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.3)',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: settings.enabled
                ? (capturing ? 'var(--precision, #4ade80)' : '#f59e0b')
                : 'var(--text-dim, #666)',
              boxShadow: settings.enabled
                ? (capturing ? '0 0 6px var(--precision, #4ade80)' : '0 0 6px #f59e0b')
                : 'none',
            }} />
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text)' }}>
              Advisor
            </span>
            {settings.enabled && (
              <span style={{ fontSize: '0.65rem', color: capturing ? 'var(--precision, #4ade80)' : '#f59e0b' }}>
                {capturing ? 'Active' : 'Waiting for screen data'}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', color: 'var(--text-dim)',
              cursor: 'pointer', fontSize: '1.2rem', padding: '0 4px',
            }}
          >
            &times;
          </button>
        </div>

        {/* Live status */}
        <div style={{
          padding: '8px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', gap: 12, fontSize: '0.65rem', color: 'var(--text-dim)',
        }}>
          <StatusPill
            label="Backend"
            ok={backendOk}
            detail={backendOk ? 'Connected' : 'Offline'}
          />
          <StatusPill
            label="Capture"
            ok={!!capturing}
            detail={screenCapture.isCapturing
              ? `Browser: ${screenCapture.framesSent} frames`
              : capturing ? `${capture!.captures_stored} frames` : 'No data'}
          />
          <StatusPill
            label="Buffer"
            ok={buffered > 0}
            detail={buffered > 0 ? `${buffered} tokens` : 'Empty'}
          />
        </div>

        {/* Screen capture preview / start button */}
        <ScreenPreview capture={screenCapture} />

        {/* Settings bar */}
        <div style={{
          padding: '10px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.enabled}
              onChange={e => updateSetting('enabled', e.target.checked)}
            />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text)' }}>
              Enable Advisor
            </span>
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', whiteSpace: 'nowrap', minWidth: 95 }}>
              Confidence: {settings.threshold.toFixed(2)}
            </span>
            <input
              type="range"
              min={0} max={1} step={0.05}
              value={settings.threshold}
              onChange={e => updateSetting('threshold', e.target.value)}
              style={{ flex: 1 }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: 'var(--text-dim)', marginTop: -4 }}>
            <span>More guidance</span>
            <span>Only high confidence</span>
          </div>
        </div>

        {/* Advisory feed */}
        <div style={{ flex: 1, overflow: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {advisories.length === 0 && (
            <div style={{ padding: '16px 4px' }}>
              {!settings.enabled ? (
                <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textAlign: 'center', lineHeight: 1.6 }}>
                  Enable the advisor to receive proactive guidance based on your screen activity.
                </div>
              ) : !capturing ? (
                <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textAlign: 'center', lineHeight: 1.6 }}>
                  Start screen capture above, then enable the advisor.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {/* Active status */}
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      padding: '4px 12px', borderRadius: 12,
                      background: 'rgba(74, 222, 128, 0.08)', border: '1px solid rgba(74, 222, 128, 0.2)',
                    }}>
                      <div style={{
                        width: 6, height: 6, borderRadius: '50%',
                        background: 'var(--precision, #4ade80)',
                        boxShadow: '0 0 6px var(--precision, #4ade80)',
                        animation: 'advisorPulse 2s ease-in-out infinite',
                      }} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--precision, #4ade80)', fontWeight: 600 }}>
                        Watching your screen
                      </span>
                    </div>
                  </div>

                  {/* Pipeline steps */}
                  <div style={{
                    background: 'var(--bg-input)', borderRadius: 6, padding: '10px 12px',
                    fontSize: '0.7rem', color: 'var(--text-dim)', lineHeight: 1.7,
                  }}>
                    <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6, fontSize: '0.7rem' }}>
                      What happens each cycle:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <StepRow n="1" text="Screen is captured and OCR'd to extract visible text" />
                      <StepRow n="2" text="Duplicate frames are discarded (nothing changed)" />
                      <StepRow n="3" text="Text is distilled into a query and checked for novelty" />
                      <StepRow n="4" text="Query runs through the neuron scoring pipeline (5 signals)" />
                      <StepRow n="5" text={`If top neuron scores above ${settings.threshold.toFixed(2)} confidence → Haiku formats guidance with citations`} />
                    </div>
                  </div>

                  {/* Notification behavior */}
                  <div style={{
                    background: 'var(--bg-input)', borderRadius: 6, padding: '10px 12px',
                    fontSize: '0.7rem', color: 'var(--text-dim)', lineHeight: 1.7,
                  }}>
                    <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6, fontSize: '0.7rem' }}>
                      How you'll be notified:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <StepRow icon="●" text="Toast notification appears in the bottom-right corner" />
                      <StepRow icon="●" text="Red badge on the advisor icon shows unread count" />
                      <StepRow icon="●" text="Click 'View Sources' on a toast to see full citations here" />
                      <StepRow icon="●" text="You can close this panel — notifications still arrive" />
                    </div>
                  </div>

                  <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)', textAlign: 'center', fontStyle: 'italic' }}>
                    Read-only — the advisor never writes to the neuron graph.
                  </div>
                </div>
              )}
            </div>
          )}
          {advisories.map(a => (
            <div key={a.id} style={{
              background: 'var(--bg-input, #0f0f23)', borderRadius: 8,
              border: '1px solid var(--border, #333)', padding: '12px 14px',
            }}>
              {/* Guidance */}
              <div style={{ fontSize: '0.82rem', color: 'var(--text)', lineHeight: 1.6, marginBottom: 8 }}>
                {a.guidance}
              </div>

              {/* Trigger */}
              <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 8, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                {a.app_id && (
                  <span style={{ background: 'var(--bg-card)', padding: '1px 5px', borderRadius: 3, border: '1px solid var(--border)' }}>
                    {a.app_id}
                  </span>
                )}
                {a.intent && (
                  <span style={{ background: 'var(--bg-card)', padding: '1px 5px', borderRadius: 3, border: '1px solid var(--border)' }}>
                    {a.intent}
                  </span>
                )}
              </div>

              {/* Citations */}
              {a.citations.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {a.citations.map(c => (
                    <div key={c.id} style={{ fontSize: '0.7rem', display: 'flex', gap: 6, alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.label}</span>
                        {c.department && (
                          <span style={{
                            marginLeft: 4, background: 'var(--bg-card)', padding: '0 3px',
                            borderRadius: 2, fontSize: '0.6rem', color: 'var(--text-dim)',
                            border: '1px solid var(--border)',
                          }}>
                            {c.department}
                          </span>
                        )}
                        <span style={{
                          marginLeft: 4, fontSize: '0.6rem', color: 'var(--text-dim)', opacity: 0.8,
                        }}>
                          {c.source_type}
                        </span>
                        {c.citation && (
                          <div style={{ color: 'var(--text-dim)', marginTop: 1, fontStyle: 'italic' }}>
                            {c.citation}
                          </div>
                        )}
                      </div>
                      <div style={{ width: 40, flexShrink: 0, textAlign: 'right' }}>
                        <div style={{ height: 3, borderRadius: 2, background: 'var(--bg-card)', overflow: 'hidden' }}>
                          <div style={{
                            height: '100%', width: `${Math.min(c.score * 100, 100)}%`,
                            background: 'var(--accent)', borderRadius: 2,
                          }} />
                        </div>
                        <div style={{ fontSize: '0.55rem', color: 'var(--text-dim)', marginTop: 1 }}>
                          {c.score.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Footer */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginTop: 8, paddingTop: 6, borderTop: '1px solid var(--border)',
              }}>
                <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>
                  {a.created_at ? new Date(a.created_at).toLocaleTimeString() : ''}
                  {a.cost_usd > 0 ? ` · $${a.cost_usd.toFixed(4)}` : ''}
                </span>
                <button
                  onClick={() => dismiss(a.id)}
                  style={{
                    padding: '2px 8px', fontSize: '0.6rem', borderRadius: 3,
                    background: 'var(--bg-card)', color: 'var(--text-dim)',
                    border: '1px solid var(--border)', cursor: 'pointer',
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '8px 16px', borderTop: '1px solid var(--border)',
          fontSize: '0.6rem', color: 'var(--text-dim)', lineHeight: 1.5,
        }}>
          Read-only — queries the neuron graph but never writes to it.
        </div>
      </div>
    </>
  );
}


function StatusPill({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{
        width: 5, height: 5, borderRadius: '50%',
        background: ok ? 'var(--precision, #4ade80)' : 'var(--text-dim, #666)',
      }} />
      <span><strong>{label}:</strong> {detail}</span>
    </div>
  );
}

function StepRow({ n, icon, text }: { n?: string; icon?: string; text: string }) {
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
      <span style={{
        minWidth: 14, textAlign: 'center',
        color: 'var(--accent)', fontWeight: 700, fontSize: '0.65rem',
      }}>
        {n ?? icon}
      </span>
      <span>{text}</span>
    </div>
  );
}

/* Inject pulse animation */
const styleEl = document.createElement('style');
styleEl.textContent = `
  @keyframes advisorPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
`;
if (!document.querySelector('[data-advisor-styles]')) {
  styleEl.setAttribute('data-advisor-styles', '');
  document.head.appendChild(styleEl);
}


