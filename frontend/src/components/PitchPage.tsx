import React, { useEffect, useState } from 'react';
import { fetchStats, fetchCostReport } from '../api';
import type { NeuronStats } from '../types';

/* ── Reusable inline styles ── */

const kpiCard: React.CSSProperties = {
  flex: '1 1 140px', textAlign: 'center', padding: '16px 12px',
  background: 'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(59,130,246,0.02) 100%)',
  borderRadius: 10, border: '1px solid rgba(59,130,246,0.15)',
};
const kpiValue: React.CSSProperties = {
  fontSize: '1.8rem', fontWeight: 700, color: '#3b82f6', lineHeight: 1.1,
};
const kpiLabel: React.CSSProperties = {
  fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase' as const,
  letterSpacing: '0.05em', marginTop: 4,
};

const pipelineStep: React.CSSProperties = {
  flex: '1 1 0', padding: '10px 8px', textAlign: 'center',
  background: 'rgba(30,41,59,0.6)', borderRadius: 8,
  border: '1px solid rgba(59,130,246,0.15)', fontSize: '0.72rem',
};
const pipelineArrow: React.CSSProperties = {
  display: 'flex', alignItems: 'center', color: '#3b82f644', fontSize: '1.2rem', padding: '0 2px',
};

const costBar = (pct: number, color: string): React.CSSProperties => ({
  height: 28, width: `${pct}%`, background: color, borderRadius: 4,
  display: 'flex', alignItems: 'center', paddingLeft: 8,
  fontSize: '0.7rem', fontWeight: 600, color: '#fff', minWidth: 60,
  transition: 'width 0.6s ease',
});

const sectionAlt: React.CSSProperties = { background: 'rgba(30,41,59,0.3)' };

const cardBase: React.CSSProperties = {
  padding: '20px 16px', borderRadius: 10,
  border: '1px solid rgba(255,255,255,0.06)',
  background: 'rgba(30,41,59,0.5)',
};

/* ── Component ── */

export default function PitchPage() {
  const [stats, setStats] = useState<NeuronStats | null>(null);
  const [cost, setCost] = useState<{ total_queries: number; total_cost_usd: number } | null>(null);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => {});
    fetchCostReport().then(setCost).catch(() => {});
  }, []);

  const depts = stats ? Object.keys(stats.by_department).length : '...';
  const roles = stats ? Object.keys(stats.by_department_roles).reduce((n, d) => n + Object.keys(stats.by_department_roles[d]).length, 0) : '...';

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 16px 80px' }}>

      {/* ── 1. Title / Hook ── */}
      <section className="about-section" style={{ textAlign: 'center', padding: '64px 0 48px' }}>
        <h1 style={{ fontSize: '3.2rem', fontWeight: 800, color: '#e2e8f0', margin: 0, letterSpacing: '-0.02em' }}>
          Corvus
        </h1>
        <p style={{ fontSize: '1.15rem', color: '#94a3b8', marginTop: 12, fontWeight: 500 }}>
          Domain intelligence that makes cheap AI perform like expensive AI
        </p>
        <p style={{ fontSize: '0.82rem', color: '#64748b', marginTop: 8 }}>
          Biomimetic knowledge retrieval for regulated industries
        </p>
      </section>

      {/* ── 2. The Problem ── */}
      <section className="about-section" style={sectionAlt}>
        <h3>The Problem</h3>
        <div className="about-thesis-grid">
          {[
            { color: '#ef4444', title: 'Frontier AI costs 60\u2013100\u00d7 more', desc: 'Organizations overpaying for every query because cheap models lack domain context.' },
            { color: '#facc15', title: 'No audit trail for regulated AI', desc: '\u201cThe AI said so\u201d doesn\u2019t pass compliance. Regulators need provenance.' },
            { color: '#22c55e', title: 'Static knowledge doesn\u2019t learn', desc: 'Same context injected whether 5% or 100% is relevant to the query.' },
          ].map((p, i) => (
            <div key={i} className="about-thesis-card">
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: p.color, marginBottom: 8 }}>{p.title}</div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>{p.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 3. The Solution ── */}
      <section className="about-section">
        <h3>The Solution</h3>
        <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.6, marginBottom: 20 }}>
          A self-improving knowledge graph that selects the right domain context for every query.
        </p>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 20 }}>
          {['Embed + Classify', 'Score', 'Spread', 'Assemble', 'Execute'].map((step, i, arr) => (
            <React.Fragment key={i}>
              <div style={pipelineStep}>{step}</div>
              {i < arr.length - 1 && <div style={pipelineArrow}>&rarr;</div>}
            </React.Fragment>
          ))}
        </div>
        <div style={{ ...kpiCard, maxWidth: 300, margin: '0 auto', textAlign: 'center' }}>
          <div style={kpiValue}>~92%</div>
          <div style={kpiLabel}>cost reduction with quality parity</div>
        </div>
      </section>

      {/* ── 4. How It Works (simplified) ── */}
      <section className="about-section" style={sectionAlt}>
        <h3>How It Works</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { title: 'Classify', desc: 'Haiku understands intent (~200ms)' },
            { title: 'Score & Select', desc: '6-signal gated scoring picks top neurons' },
            { title: 'Assemble & Execute', desc: 'Token-budgeted prompt \u2192 LLM responds with enriched context' },
          ].map((s, i) => (
            <div key={i} style={cardBase}>
              <div style={{ fontWeight: 700, color: '#e2e8f0', marginBottom: 6, fontSize: '0.88rem' }}>{s.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.5 }}>{s.desc}</div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 14, textAlign: 'center' }}>
          The only non-deterministic step is the final LLM generation.
        </p>
      </section>

      {/* ── 5. Traction / Proof Points ── */}
      <section className="about-section">
        <h3>Traction / Proof Points</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 24 }}>
          {[
            { label: 'Neurons', value: stats?.total_neurons ?? '...' },
            { label: 'Departments', value: depts },
            { label: 'Roles', value: roles },
            { label: 'Queries', value: cost?.total_queries ?? '...' },
            { label: 'Firings', value: stats?.total_firings ?? '...' },
            { label: 'Total Cost', value: cost ? `$${cost.total_cost_usd.toFixed(2)}` : '...' },
          ].map((k, i) => (
            <div key={i} style={kpiCard}>
              <div style={kpiValue}>{k.value}</div>
              <div style={kpiLabel}>{k.label}</div>
            </div>
          ))}
        </div>

        <h4 style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: 10 }}>Cost per Query: Raw Opus vs Corvus (total)</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Raw Opus bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 90, fontSize: '0.7rem', color: '#94a3b8', textAlign: 'right', flexShrink: 0 }}>Raw Opus</div>
            <div style={{ flex: 1 }}>
              <div style={costBar(100, '#ef4444')}>$1.00</div>
            </div>
          </div>
          {/* Corvus stacked bar — all components totaled */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 90, fontSize: '0.7rem', color: '#94a3b8', textAlign: 'right', flexShrink: 0 }}>Corvus</div>
            <div style={{ flex: 1, display: 'flex', borderRadius: 4, overflow: 'hidden', height: 28 }}>
              <div style={{ width: '6%', background: '#3b82f6', display: 'flex', alignItems: 'center', paddingLeft: 6, fontSize: '0.62rem', fontWeight: 600, color: '#fff', minWidth: 50 }} title="Haiku classification + scoring">Classify</div>
              <div style={{ width: '1.5%', background: '#22c55e', display: 'flex', alignItems: 'center', fontSize: '0.62rem', fontWeight: 600, color: '#fff', minWidth: 40 }} title="Haiku execution">Exec</div>
              <div style={{ width: '0.5%', background: '#a855f6', minWidth: 20 }} title="Spread + assembly (deterministic, ~$0)" />
            </div>
            <div style={{ fontSize: '0.7rem', color: '#3b82f6', fontWeight: 600, flexShrink: 0 }}>$0.08</div>
          </div>
        </div>
        <p style={{ fontSize: '0.68rem', color: '#64748b', marginTop: 8, lineHeight: 1.5 }}>
          Corvus total broken out: <span style={{ color: '#3b82f6' }}>Classify</span> (Haiku ~$0.05) +{' '}
          <span style={{ color: '#22c55e' }}>Execute</span> (Haiku ~$0.03) +{' '}
          <span style={{ color: '#a855f6' }}>Score/Spread/Assemble</span> (deterministic, ~$0).
          MCP context mode drops to ~$0.00005; structural fast path is $0.
        </p>

        <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.12)' }}>
          <div style={{ fontSize: '0.78rem', color: '#cbd5e1', fontWeight: 600, marginBottom: 6 }}>Statistical Quality Findings</div>
          <p style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.6, margin: 0 }}>
            Blind A/B evaluation (model identity hidden, scored on accuracy, completeness, clarity, and faithfulness)
            with <strong style={{ color: '#cbd5e1' }}>Benjamini-Hochberg FDR correction</strong> across 6 simultaneous tests,
            Cohen&rsquo;s d effect size reporting, and statistical power analysis.
            Corvus + Haiku achieves quality parity with raw Opus at the 95% confidence level across domain queries &mdash;
            the ~92% cost reduction comes with no statistically significant loss in answer quality.
          </p>
        </div>
      </section>

      {/* ── 6. The Compliance Advantage ── */}
      <section className="about-section" style={sectionAlt}>
        <h3>The Compliance Advantage</h3>
        <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.6, marginBottom: 20, fontWeight: 600 }}>
          Every other graph-RAG answers &ldquo;does it work?&rdquo; &mdash; Corvus also answers &ldquo;can we deploy it?&rdquo;
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
          {[
            { name: 'NIST AI RMF', status: 'Aligned', color: '#22c55e', desc: 'Traceability, explainability, provenance' },
            { name: 'AIUC-1', status: 'Assessed', color: '#3b82f6', desc: '48 requirements (33% addressed, 33% partial)' },
            { name: 'FedRAMP Moderate', status: 'Roadmapped', color: '#f59e0b', desc: '259 controls' },
            { name: 'SOC 2 Type II', status: 'Roadmapped', color: '#f59e0b', desc: '51 criteria' },
            { name: 'CMMC Level 2', status: 'Roadmapped', color: '#f59e0b', desc: '110 practices' },
            { name: 'NASA/JPL', status: 'Enforced', color: '#22c55e', desc: 'Automated linting, pre-commit hooks' },
          ].map((f, i) => (
            <div key={i} style={cardBase}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.85rem' }}>{f.name}</span>
                <span style={{
                  fontSize: '0.65rem', fontWeight: 600, color: f.color,
                  border: `1px solid ${f.color}44`, borderRadius: 6, padding: '2px 8px',
                }}>{f.status}</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{f.desc}</div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 16, textAlign: 'center', fontWeight: 500 }}>
          Full provenance. Human-in-the-loop. Advisory-only LLM. No auto-magic.
        </p>
      </section>

      {/* ── 7. Market Opportunity ── */}
      <section className="about-section">
        <h3>Market Opportunity</h3>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, marginBottom: 20 }}>
          {[
            { label: 'TAM: Enterprise AI spending', size: '$200B+ by 2027', width: '100%', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.2)' },
            { label: 'SAM: Regulated industry AI', size: '~$40B', width: '60%', bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.2)' },
            { label: 'SOM: Knowledge mgmt + compliance AI (defense/aerospace)', size: '~$2\u20135B', width: '30%', bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.2)' },
          ].map((t, i) => (
            <div key={i} style={{
              width: t.width, padding: '14px 16px', borderRadius: 8,
              background: t.bg, border: `1px solid ${t.border}`, textAlign: 'center',
            }}>
              <div style={{ fontSize: '0.78rem', color: '#e2e8f0', fontWeight: 600 }}>{t.label}</div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: 2 }}>{t.size}</div>
            </div>
          ))}
        </div>
        <p style={{ fontSize: '0.78rem', color: '#94a3b8', fontStyle: 'italic', textAlign: 'center' }}>
          &ldquo;Every org using AI in a regulated environment needs auditability. None of the current solutions provide it.&rdquo;
        </p>
      </section>

      {/* ── 8. Competitive Landscape ── */}
      <section className="about-section" style={sectionAlt}>
        <h3>Competitive Landscape</h3>
        <div style={{ position: 'relative', maxWidth: 500, margin: '0 auto' }}>
          {/* Axis labels */}
          <div style={{ position: 'absolute', left: -10, top: '50%', transform: 'rotate(-90deg) translateX(50%)', fontSize: '0.65rem', color: '#64748b', whiteSpace: 'nowrap' }}>
            Cost: High &rarr; Low
          </div>
          <div style={{ textAlign: 'center', fontSize: '0.65rem', color: '#64748b', marginTop: 8 }}>
            Compliance: None &rarr; Full
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginLeft: 20 }}>
            {[
              { label: 'Raw LLMs', sub: 'High cost, no compliance', color: '#ef4444', highlight: false },
              { label: 'Enterprise RAG Platforms', sub: 'High cost, some compliance', color: '#fb923c', highlight: false },
              { label: 'Open-Source Graph-RAG', sub: 'Moderate cost, no compliance', color: '#94a3b8', highlight: false },
              { label: 'Corvus', sub: 'Low cost, compliance-first', color: '#3b82f6', highlight: true },
            ].map((q, i) => (
              <div key={i} style={{
                ...cardBase,
                borderColor: q.highlight ? '#3b82f6' : 'rgba(255,255,255,0.06)',
                borderWidth: q.highlight ? 2 : 1,
                boxShadow: q.highlight ? '0 0 20px rgba(59,130,246,0.15)' : 'none',
              }}>
                <div style={{ fontWeight: 700, color: q.color, fontSize: '0.82rem', marginBottom: 4 }}>{q.label}</div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{q.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 9. Technology Moat ── */}
      <section className="about-section">
        <h3>Technology Moat</h3>
        <div className="about-thesis-grid">
          {[
            { color: '#8b5cf6', title: '6-Signal Gated Scoring', desc: 'Biomimetic architecture with 5 academic convergence points.' },
            { color: '#3b82f6', title: '2,180+ Curated Domain Neurons', desc: 'Institutional knowledge, not auto-extracted.' },
            { color: '#22c55e', title: 'Compliance Infrastructure', desc: 'NIST / AIUC-1 / FedRAMP / SOC 2 / CMMC roadmap built-in.' },
            { color: '#f59e0b', title: 'Self-Improving Loop', desc: 'Graph learns from usage, discovers gaps, grows at point of need.' },
          ].map((m, i) => (
            <div key={i} className="about-thesis-card">
              <div style={{ fontSize: '1rem', fontWeight: 700, color: m.color, marginBottom: 8 }}>{m.title}</div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>{m.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 10. Business Model ── */}
      <section className="about-section" style={sectionAlt}>
        <h3>Business Model</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
          {[
            { title: 'Internal Licensing', price: '$5\u201315K/month per org', desc: 'On-prem deployment with support' },
            { title: 'SaaS (Multi-Tenant)', price: '$20K/month base + per-query', desc: 'Hosted, managed, auto-scaling' },
            { title: 'Research Licensing', price: '$50K\u2013150K/year', desc: 'Academic & lab partnerships' },
          ].map((r, i) => (
            <div key={i} style={cardBase}>
              <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.85rem', marginBottom: 6 }}>{r.title}</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#3b82f6', marginBottom: 6 }}>{r.price}</div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{r.desc}</div>
            </div>
          ))}
        </div>
        <div style={{
          padding: '14px 18px', borderRadius: 8,
          background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)',
          fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.6, textAlign: 'center',
        }}>
          The neuron corpus is the moat &mdash; recreating 2,180+ curated domain neurons requires the same research regardless of engineering talent.
        </div>
      </section>

      {/* ── 11. Roadmap ── */}
      <section className="about-section">
        <h3>Roadmap</h3>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {[
            { phase: 'Now', color: '#22c55e', items: 'Core platform + compliance framework + 2,180 neurons' },
            { phase: 'Next', color: '#3b82f6', items: 'Production hardening (auth, rate limiting, PII scanning)' },
            { phase: 'Future', color: '#a855f6', items: 'Multi-tenant SaaS, third-party audit, cross-domain expansion' },
          ].map((p, i) => (
            <div key={i} style={{ flex: '1 1 0', minWidth: 200, ...cardBase, borderColor: `${p.color}33` }}>
              <div style={{
                fontSize: '0.7rem', fontWeight: 700, color: p.color, textTransform: 'uppercase' as const,
                letterSpacing: '0.06em', marginBottom: 8,
              }}>
                {p.phase}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>{p.items}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 12. Call to Action ── */}
      <section className="about-section" style={{ ...sectionAlt, textAlign: 'center', padding: '48px 0' }}>
        <h3>Get Involved</h3>
        <p style={{ fontSize: '1.05rem', color: '#e2e8f0', fontWeight: 600, marginBottom: 8 }}>
          Corvus is ready for its first deployment partner.
        </p>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: 20 }}>
          Regulated industries need AI they can audit, explain, and afford.
        </p>
        <a
          href="https://github.com/tylerbvogel-max/Corvus-2.0"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block', padding: '10px 24px', borderRadius: 8,
            background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)',
            color: '#3b82f6', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none',
          }}
        >
          github.com/tylerbvogel-max/Corvus-2.0
        </a>
      </section>

    </div>
  );
}
