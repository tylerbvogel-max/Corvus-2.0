import { useState, useEffect, useCallback, useRef } from 'react';

const CORVUS_API = '/corvus';
const POLL_INTERVAL = 5000;
const TOAST_DURATION = 10000;

interface Advisory {
  id: number;
  guidance: string;
  intent: string | null;
  app_id: string | null;
  created_at: string | null;
}

interface Props {
  panelOpen: boolean;
  onOpenPanel: () => void;
  onUnreadChange: (count: number) => void;
}

export default function AdvisorToast({ panelOpen, onOpenPanel, onUnreadChange }: Props) {
  const [toast, setToast] = useState<Advisory | null>(null);
  const [visible, setVisible] = useState(false);
  const lastSeenIdRef = useRef<number>(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const dismissRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const unreadRef = useRef(0);

  const checkForNew = useCallback(async () => {
    try {
      const r = await fetch(`${CORVUS_API}/advisories/current`);
      if (!r.ok) return;
      const data = await r.json();
      if (!data || !data.id) return;

      if (data.id > lastSeenIdRef.current) {
        lastSeenIdRef.current = data.id;

        // Only show toast if panel is closed
        if (!panelOpen) {
          unreadRef.current += 1;
          onUnreadChange(unreadRef.current);
          setToast(data);
          setVisible(true);

          // Auto-dismiss after duration
          if (dismissRef.current) clearTimeout(dismissRef.current);
          dismissRef.current = setTimeout(() => setVisible(false), TOAST_DURATION);
        }
      }
    } catch {
      // Backend unreachable — silent
    }
  }, [panelOpen, onUnreadChange]);

  // Poll for new advisories
  useEffect(() => {
    pollRef.current = setInterval(checkForNew, POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, [checkForNew]);

  // Clear unread when panel opens
  useEffect(() => {
    if (panelOpen) {
      unreadRef.current = 0;
      onUnreadChange(0);
      setVisible(false);
      if (dismissRef.current) clearTimeout(dismissRef.current);
    }
  }, [panelOpen, onUnreadChange]);

  const dismissToast = useCallback(() => {
    setVisible(false);
    if (dismissRef.current) clearTimeout(dismissRef.current);
  }, []);

  const viewInPanel = useCallback(() => {
    dismissToast();
    onOpenPanel();
  }, [dismissToast, onOpenPanel]);

  if (!visible || !toast) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20, zIndex: 1100,
      width: 360, maxWidth: 'calc(100vw - 40px)',
      background: 'var(--bg-card, #1a1a2e)',
      border: '1px solid var(--accent)',
      borderRadius: 10,
      boxShadow: '0 8px 32px rgba(0,0,0,0.4), 0 0 12px rgba(99,102,241,0.15)',
      animation: 'advisorToastIn 0.3s ease-out',
      overflow: 'hidden',
    }}>
      {/* Accent bar */}
      <div style={{ height: 3, background: 'var(--accent)' }} />

      <div style={{ padding: '12px 14px' }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 8,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="2" fill="var(--accent)" />
              <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
              <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
            </svg>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Advisor
            </span>
            {toast.app_id && (
              <span style={{
                fontSize: '0.6rem', color: 'var(--text-dim)',
                background: 'var(--bg-input)', padding: '1px 5px', borderRadius: 3,
              }}>
                {toast.app_id}
              </span>
            )}
          </div>
          <button
            onClick={dismissToast}
            style={{
              background: 'none', border: 'none', color: 'var(--text-dim)',
              cursor: 'pointer', fontSize: '1rem', padding: '0 2px', lineHeight: 1,
            }}
          >
            &times;
          </button>
        </div>

        {/* Guidance text */}
        <div style={{
          fontSize: '0.8rem', color: 'var(--text)', lineHeight: 1.6,
          marginBottom: 10,
        }}>
          {toast.guidance}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={viewInPanel}
            style={{
              padding: '4px 12px', borderRadius: 4,
              background: 'var(--accent)', color: '#000',
              border: 'none', cursor: 'pointer',
              fontSize: '0.7rem', fontWeight: 600,
            }}
          >
            View Sources
          </button>
          <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)' }}>
            {toast.created_at ? new Date(toast.created_at).toLocaleTimeString() : ''}
          </span>
        </div>
      </div>

      <style>{`
        @keyframes advisorToastIn {
          from { opacity: 0; transform: translateY(16px) scale(0.96); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );
}
