import { useState, useCallback, useEffect } from 'react'
import Explorer from './components/Explorer'
import Dashboard from './components/Dashboard'
import QueryLab from './components/QueryLab'
import EvaluationPage from './components/EvaluationPage'
import RefinementHistory from './components/RefinementHistory'
import AutopilotPage from './components/AutopilotPage'
import CirclePacking from './components/CirclePacking'
import SampleQueries from './components/SampleQueries'
import QualityPage from './components/QualityPage'
import FairnessPage from './components/FairnessPage'
import PerformancePage from './components/PerformancePage'
import EmergentQueuePage from './components/EmergentQueuePage'
import SynapticLearningPage from './components/SynapticLearningPage'
import LayerHeatmap from './components/LayerHeatmap'
import NeuronUniverse from './components/NeuronUniverse'
import KnowledgeGovernancePage from './components/KnowledgeGovernancePage'
import HomePage from './components/HomePage'
import SystemUseBanner from './components/SystemUseBanner'
import EngramPage from './components/EngramPage'
import CorvusPage from './components/CorvusPage'
import ObservationReviewPage from './components/ObservationReviewPage'

import { fetchTenantConfig, fetchAllTenants } from './config'
import type { TenantConfig, TenantSummary } from './config'
import { checkAccess, setAccessKey, getAccessKey } from './auth'

type Tab = 'home' | 'explorer' | 'graph' | 'universe' | 'dashboard' | 'layer-heatmap' | 'query' | 'samples' | 'evaluation' | 'refinements' | 'autopilot' | 'emergent-queue' | 'synaptic-learning' | 'quality' | 'fairness' | 'performance' | 'knowledge-governance' | 'engrams' | 'corvus-feed' | 'corvus-observations';

type Theme = 'corvus-native' | 'corvus-dark' | 'corvus-light' | 'high-contrast' | 'colorblind';

const THEME_LABELS: Record<Theme, string> = {
  'corvus-native': 'Corvus Native',
  'corvus-dark': 'Corvus',
  'corvus-light': 'Corvus Light',
  'high-contrast': 'High Contrast',
  'colorblind': 'Colorblind',
};

interface NavItem {
  key: Tab;
  label: string;
  className?: string;
  labelColor?: string;
}

function buildNavGroups(tenantId: string | undefined): { label: string; items: NavItem[] }[] {
  const groups: { label: string; items: NavItem[] }[] = [];

  // Screen Watcher — only for tenants with screen capture enabled
  if (tenantId === 'corvus-apex') {
    groups.push({
      label: 'Corvus',
      items: [
        { key: 'corvus-feed', label: 'Screen Watcher' },
        { key: 'corvus-observations', label: 'Observations' },
      ],
    });
  }

  groups.push(
    {
      label: 'Workbench',
      items: [
        { key: 'query', label: 'Query Lab' },
        { key: 'samples', label: 'Samples' },
        { key: 'autopilot', label: 'Autopilot' },
        { key: 'refinements', label: 'Refinements' },
        { key: 'emergent-queue', label: 'Emergent Queue' },
        { key: 'synaptic-learning', label: 'Synaptic Learning' },
      ],
    },
    {
      label: 'Knowledge',
      items: [
        { key: 'explorer', label: 'Explorer' },
        { key: 'engrams', label: 'Engrams' },
        { key: 'graph', label: 'Graph' },
        { key: 'universe', label: '3D Universe' },
        { key: 'dashboard', label: 'Dashboard' },
        { key: 'layer-heatmap', label: 'Layer Heatmap' },
      ],
    },
    {
      label: 'Evaluate',
      items: [
        { key: 'knowledge-governance', label: 'Governance' },
        { key: 'performance', label: 'Performance' },
        { key: 'quality', label: 'Quality' },
        { key: 'fairness', label: 'Fairness' },
        { key: 'evaluation', label: 'Evaluation' },
      ],
    },
  );

  return groups;
}

function getInitialTheme(): Theme {
  const saved = localStorage.getItem('corvus-theme');
  if (saved && saved in THEME_LABELS) {
    return saved as Theme;
  }
  return 'corvus-native';
}

export default function App() {
  const [tab, setTab] = useState<Tab>('home');
  const [explorerNeuronId, setExplorerNeuronId] = useState<number | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    () => new Set()
  );
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);
  const [tenantConfig, setTenantConfig] = useState<TenantConfig | null>(null);
  const [allTenants, setAllTenants] = useState<TenantSummary[]>([]);
  const [authStatus, setAuthStatus] = useState<'checking' | 'open' | 'valid' | 'needs_key'>('checking');
  const [keyInput, setKeyInput] = useState('');
  const [keyError, setKeyError] = useState(false);

  // Check auth on mount
  useEffect(() => {
    checkAccess().then(status => {
      if (status === 'invalid' && !getAccessKey()) setAuthStatus('needs_key');
      else if (status === 'invalid') setAuthStatus('needs_key');
      else setAuthStatus(status);
    });
  }, []);

  // Fetch tenant config + all tenants once authed
  useEffect(() => {
    if (authStatus === 'open' || authStatus === 'valid') {
      fetchTenantConfig().then(setTenantConfig);
      fetchAllTenants().then(setAllTenants);
    }
  }, [authStatus]);

  const displayName = tenantConfig?.display_name ?? 'Corvus';
  const otherTenants = allTenants.filter(t => t.tenant_id !== tenantConfig?.tenant_id);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('corvus-theme', theme);
  }, [theme]);

  function setTheme(t: Theme) {
    setThemeState(t);
    setThemeMenuOpen(false);
  }

  function navigateToNeuron(id: number) {
    setExplorerNeuronId(id);
    setTab('explorer');
  }

  const toggleGroup = useCallback((label: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }, []);

  // Build nav groups based on tenant (screen watcher only for apex)
  const navGroups = buildNavGroups(tenantConfig?.tenant_id);
  const activeGroup = navGroups.find(g => g.items.some(i => i.key === tab))?.label;

  // Auth gate
  if (authStatus === 'checking') {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-dim)' }}>Loading...</div>;
  }

  if (authStatus === 'needs_key') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
        <div style={{ textAlign: 'center', maxWidth: 360 }}>
          <img src="/corvus-logo.png" alt="Corvus" style={{ width: 64, height: 64, marginBottom: 16, opacity: 0.8 }} />
          <h2 style={{ color: 'var(--text)', fontSize: 18, margin: '0 0 8px' }}>Corvus Access</h2>
          <p style={{ color: 'var(--text-dim)', fontSize: 13, margin: '0 0 20px' }}>Enter your access key to continue.</p>
          <form onSubmit={e => {
            e.preventDefault();
            setAccessKey(keyInput);
            setKeyError(false);
            checkAccess().then(status => {
              if (status === 'valid' || status === 'open') setAuthStatus(status);
              else { setKeyError(true); setKeyInput(''); }
            });
          }}>
            <input
              type="password"
              value={keyInput}
              onChange={e => setKeyInput(e.target.value)}
              placeholder="Access key"
              autoFocus
              style={{
                width: '100%', padding: '10px 14px', fontSize: 14,
                background: 'var(--bg-input)', border: `1px solid ${keyError ? '#ef4444' : 'var(--border)'}`,
                borderRadius: 8, color: 'var(--text)', outline: 'none',
                marginBottom: 12, fontFamily: 'monospace',
              }}
            />
            {keyError && <p style={{ color: '#ef4444', fontSize: 12, margin: '0 0 12px' }}>Invalid access key</p>}
            <button type="submit" style={{
              width: '100%', padding: '10px', fontSize: 14, fontWeight: 600,
              background: 'var(--accent, #c87533)', color: '#fff', border: 'none',
              borderRadius: 8, cursor: 'pointer',
            }}>
              Enter
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app app-sidebar-layout">
      <SystemUseBanner />
      <aside className={`sidebar${collapsed ? ' sidebar-collapsed' : ''}`}>
        <div className="sidebar-header">
          <img src="/corvus-logo-128.png" alt="Corvus" className="sidebar-logo" onClick={() => setTab('home')} style={{ cursor: 'pointer' }} />
          {!collapsed && <h1 className="app-title" onClick={() => setTab('home')} style={{ cursor: 'pointer' }}>{displayName}</h1>}
          <button
            className="sidebar-toggle"
            onClick={() => setCollapsed(c => !c)}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? '\u25B6' : '\u25C0'}
          </button>
        </div>
        {!collapsed && otherTenants.length > 0 && (
          <div className="tenant-switcher">
            {otherTenants.map(t => (
              <a
                key={t.tenant_id}
                href={t.default_port ? `http://localhost:${t.default_port}` : '#'}
                className="tenant-switcher-link"
                title={`Switch to ${t.display_name}`}
              >
                {t.display_name} &rarr;
              </a>
            ))}
          </div>
        )}
        {!collapsed && (
          <nav className="sidebar-nav">
            {navGroups.map(group => (
              <div key={group.label} className={`sidebar-group${activeGroup === group.label ? ' sidebar-group-active' : ''}`}>
                <button
                  className="sidebar-group-header"
                  onClick={() => toggleGroup(group.label)}
                >
                  <span className="sidebar-chevron">{expandedGroups.has(group.label) ? '\u25BE' : '\u25B8'}</span>
                  <span>{group.label}</span>
                </button>
                {expandedGroups.has(group.label) && (
                  <div className="sidebar-group-items">
                    {group.items.map(item => (
                      <button
                        key={item.key}
                        className={`sidebar-item${tab === item.key ? ' active' : ''}${item.className ? ' ' + item.className : ''}`}
                        onClick={() => setTab(item.key)}
                      >
                        {item.labelColor ? <span style={{ color: item.labelColor }}>{item.label}</span> : item.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        )}
        {/* Project info — always visible, even when collapsed */}
        {!collapsed && (
          <div className="sidebar-info-area" style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted, #888)', borderTop: '1px solid var(--border, #333)', marginTop: 'auto' }}>
            <div style={{ marginBottom: 2, opacity: 0.7 }}>Running at <strong>http://localhost:8002</strong></div>
            <a href="https://github.com/tylerbvogel-max/Corvus-2.0" target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'monospace', fontSize: '10px', opacity: 0.5, color: 'inherit', textDecoration: 'none' }} onMouseEnter={e => (e.currentTarget.style.opacity = '0.8')} onMouseLeave={e => (e.currentTarget.style.opacity = '0.5')}>github.com/tylerbvogel-max/Corvus-2.0</a>
          </div>
        )}
        {/* Settings gear — always visible, even when collapsed */}
        <div className="sidebar-settings-area">
          <button
            className="sidebar-settings-btn"
            onClick={() => setThemeMenuOpen(o => !o)}
            title="Settings"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </div>
      </aside>

      {/* Settings popup */}
      {themeMenuOpen && (
        <>
          <div className="settings-overlay" onClick={() => setThemeMenuOpen(false)} />
          <div className="settings-popup">
            <div className="settings-popup-header">
              <span>Settings</span>
              <button className="settings-popup-close" onClick={() => setThemeMenuOpen(false)}>&times;</button>
            </div>
            <div className="settings-popup-section">
              <label className="settings-label">Theme</label>
              <div className="settings-theme-options">
                {(Object.keys(THEME_LABELS) as Theme[]).map(t => (
                  <button
                    key={t}
                    className={`settings-theme-btn${theme === t ? ' active' : ''}`}
                    onClick={() => setTheme(t)}
                  >
                    <span className={`settings-theme-swatch settings-theme-swatch--${t}`} />
                    <span>{THEME_LABELS[t]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
      <main className="app-main">
        {tab === 'home' && <HomePage onNavigate={k => setTab(k as Tab)} />}
        {tab === 'corvus-feed' && <CorvusPage />}
        {tab === 'corvus-observations' && <ObservationReviewPage />}
        {tab === 'explorer' && <Explorer navigateToNeuronId={explorerNeuronId} onNavigateHandled={() => setExplorerNeuronId(null)} />}
        {tab === 'engrams' && <EngramPage />}
        {tab === 'graph' && <CirclePacking />}
        {tab === 'universe' && <NeuronUniverse />}
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'layer-heatmap' && <LayerHeatmap />}
        <div style={{ display: tab === 'query' ? 'contents' : 'none' }}><QueryLab onNavigateToNeuron={navigateToNeuron} /></div>
        {tab === 'evaluation' && <EvaluationPage />}
        {tab === 'refinements' && <RefinementHistory />}
        {tab === 'samples' && <SampleQueries />}
        {tab === 'autopilot' && <AutopilotPage />}
        {tab === 'emergent-queue' && <EmergentQueuePage />}
        {tab === 'synaptic-learning' && <SynapticLearningPage />}
        {tab === 'quality' && <QualityPage />}
        {tab === 'fairness' && <FairnessPage />}
        {tab === 'performance' && <PerformancePage />}
        {tab === 'knowledge-governance' && <KnowledgeGovernancePage />}
      </main>
    </div>
  )
}


