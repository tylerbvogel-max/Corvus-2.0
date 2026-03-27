import { useEffect, useRef, useState } from 'react'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, LogarithmicScale, Tooltip, Legend } from 'chart.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, LogarithmicScale, Tooltip, Legend);

interface ModelTokens {
  label: string;
  mode: string;
  color: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
  durationMs: number;
  neurons: boolean;
  tokenBudget: number | null;
}

function formatTokensPerDollar(val: number): string {
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M';
  if (val >= 1_000) return (val / 1_000).toFixed(0) + 'K';
  return val.toFixed(0);
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${rem.toFixed(0)}s`;
}

/** Darken a hex color by mixing toward black */
function darkenColor(hex: string, amount: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const dr = Math.max(0, Math.round(r * (1 - amount)));
  const dg = Math.max(0, Math.round(g * (1 - amount)));
  const db = Math.max(0, Math.round(b * (1 - amount)));
  return `#${dr.toString(16).padStart(2, '0')}${dg.toString(16).padStart(2, '0')}${db.toString(16).padStart(2, '0')}`;
}

export default function TokenCharts({ models, baseline, totalElapsedMs }: { models: ModelTokens[]; baseline: string; totalElapsedMs?: number }) {
  const tokenRef = useRef<HTMLCanvasElement>(null);
  const costRef = useRef<HTMLCanvasElement>(null);
  const tokenChart = useRef<Chart | null>(null);
  const costChart = useRef<Chart | null>(null);
  const [logScale, setLogScale] = useState(false);

  useEffect(() => {
    const labels = models.map(m => m.label);
    const colors = models.map(m => m.color);
    const style = getComputedStyle(document.documentElement);
    const textColor = style.getPropertyValue('--text').trim() || '#c8d0dc';
    const textDimColor = style.getPropertyValue('--text-dim').trim() || '#c8d0dc';
    const gridColor = style.getPropertyValue('--border').trim() || '#1e2d4a';

    const baselineSlot = models.find(m => m.mode === baseline);
    const baselineCost = baselineSlot?.cost ?? 0;
    const baselineTotalTokens = baselineSlot ? baselineSlot.inputTokens + baselineSlot.outputTokens : 0;
    const baselineTPD = baselineCost > 0 ? baselineTotalTokens / baselineCost : 0;

    const yScaleType = logScale ? 'logarithmic' as const : 'linear' as const;

    // ── Stacked Token Chart ──
    if (tokenRef.current) {
      tokenChart.current?.destroy();
      tokenChart.current = new Chart(tokenRef.current, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Input Tokens',
              data: models.map(m => m.inputTokens),
              backgroundColor: colors.map(c => c + '99'),
              borderColor: colors,
              borderWidth: 1,
              borderRadius: { topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4 },
            },
            {
              label: 'Output Tokens',
              data: models.map(m => m.outputTokens),
              backgroundColor: colors.map(c => darkenColor(c.replace(/[^#0-9a-fA-F]/g, '').slice(0, 7), 0.4) + 'cc'),
              borderColor: colors.map(c => darkenColor(c.replace(/[^#0-9a-fA-F]/g, '').slice(0, 7), 0.5)),
              borderWidth: 1,
              borderRadius: { topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 },
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: { color: textDimColor, font: { size: 10 }, boxWidth: 12, padding: 8 },
            },
            tooltip: {
              callbacks: {
                label: (ctx) => `${ctx.dataset.label}: ${(ctx.parsed.y ?? 0).toLocaleString()} tokens`,
                afterBody: (items) => {
                  const idx = items[0]?.dataIndex;
                  if (idx == null) return '';
                  const m = models[idx];
                  return `Total: ${(m.inputTokens + m.outputTokens).toLocaleString()} tokens`;
                },
              },
            },
          },
          scales: {
            y: {
              type: yScaleType,
              stacked: !logScale,
              beginAtZero: !logScale,
              title: { display: true, text: 'Tokens', color: textDimColor, font: { size: 11 } },
              ticks: {
                color: textDimColor,
                maxTicksLimit: 12,
              },
              grid: { color: gridColor },
            },
            x: {
              stacked: !logScale,
              ticks: { color: textColor, font: { weight: 'bold' }, maxRotation: 45, minRotation: 0 },
              grid: { display: false },
            },
          },
        },
      });
    }

    // ── Cost Chart ──
    if (costRef.current) {
      costChart.current?.destroy();
      costChart.current = new Chart(costRef.current, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Cost (USD)',
            data: models.map(m => m.cost),
            backgroundColor: colors.map(c => c + '99'),
            borderColor: colors,
            borderWidth: 1,
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `$${(ctx.parsed.y ?? 0).toFixed(6)}`,
                afterBody: (items) => {
                  const idx = items[0]?.dataIndex;
                  if (idx == null) return [];
                  const m = models[idx];
                  const totalTokens = m.inputTokens + m.outputTokens;
                  const tpd = m.cost > 0 ? totalTokens / m.cost : 0;
                  const lines = [`${formatTokensPerDollar(tpd)} tokens/$`];
                  if (baselineSlot && m.mode !== baseline && baselineCost > 0) {
                    const diff = m.cost - baselineCost;
                    const pct = (diff / baselineCost) * 100;
                    const cheaper = diff < 0;
                    lines.push('');
                    lines.push(`vs ${baselineSlot.label}:`);
                    lines.push(`${cheaper ? '' : '+'}${pct.toFixed(0)}% (${cheaper ? 'cheaper' : 'more expensive'})`);
                    if (baselineTPD > 0) {
                      lines.push(`${(tpd / baselineTPD).toFixed(1)}x tokens/$ efficiency`);
                    }
                  }
                  if (m.durationMs > 0) lines.push(`${formatDuration(m.durationMs)}`);
                  return lines;
                },
              },
            },
          },
          scales: {
            y: {
              type: yScaleType,
              beginAtZero: !logScale,
              title: { display: true, text: 'Cost (USD)', color: textDimColor, font: { size: 11 } },
              ticks: {
                color: textDimColor,
                maxTicksLimit: 10,
                callback: (value) => `$${Number(value).toFixed(4)}`,
              },
              grid: { color: gridColor },
            },
            x: {
              ticks: { color: textColor, font: { weight: 'bold' }, maxRotation: 45, minRotation: 0 },
              grid: { display: false },
            },
          },
        },
      });
    }

    return () => {
      tokenChart.current?.destroy();
      costChart.current?.destroy();
    };
  }, [models, baseline, logScale]);

  const totalCost = models.reduce((sum, m) => sum + m.cost, 0);

  return (
    <div className="token-charts">
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 6 }}>
        <label style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
          <input type="checkbox" checked={logScale} onChange={e => setLogScale(e.target.checked)} />
          Log scale
        </label>
      </div>
      <div className="token-charts-grid">
        <div className="token-chart-box">
          <div className="token-chart-title">Tokens by Model</div>
          <div className="token-chart-canvas" style={{ height: 280 }}><canvas ref={tokenRef} /></div>
        </div>
        <div className="token-chart-box">
          <div className="token-chart-title">Cost by Model</div>
          <div className="token-chart-canvas" style={{ height: 280 }}><canvas ref={costRef} /></div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: 8 }}>
        <span>Total: <strong style={{ color: 'var(--text)' }}>${totalCost.toFixed(6)}</strong></span>
        {totalElapsedMs != null && totalElapsedMs > 0 && (
          <span>Pipeline: <strong style={{ color: 'var(--accent)' }}>{formatDuration(totalElapsedMs)}</strong></span>
        )}
      </div>
    </div>
  );
}
