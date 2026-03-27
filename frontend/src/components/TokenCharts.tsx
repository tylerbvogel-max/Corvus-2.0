import { useEffect, useRef } from 'react'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

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

export default function TokenCharts({ models, baseline, totalElapsedMs }: { models: ModelTokens[]; baseline: string; totalElapsedMs?: number }) {
  const tokenRef = useRef<HTMLCanvasElement>(null);
  const costRef = useRef<HTMLCanvasElement>(null);
  const tokenChart = useRef<Chart | null>(null);
  const costChart = useRef<Chart | null>(null);

  useEffect(() => {
    const labels = models.map(m => m.label);
    const colors = models.map(m => m.color);
    const style = getComputedStyle(document.documentElement);
    const textColor = style.getPropertyValue('--text').trim() || '#c8d0dc';
    const textDimColor = style.getPropertyValue('--text-dim').trim() || '#c8d0dc';
    const gridColor = style.getPropertyValue('--border').trim() || '#1e2d4a';

    // Baseline data for cost tooltip
    const baselineSlot = models.find(m => m.mode === baseline);
    const baselineCost = baselineSlot?.cost ?? 0;
    const baselineTotalTokens = baselineSlot ? baselineSlot.inputTokens + baselineSlot.outputTokens : 0;
    const baselineTPD = baselineCost > 0 ? baselineTotalTokens / baselineCost : 0;

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
              backgroundColor: colors.map(c => c + '77'),
              borderColor: colors,
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
                label: (ctx) => {
                  const val = (ctx.parsed.y ?? 0).toLocaleString();
                  return `${ctx.dataset.label}: ${val} tokens`;
                },
                afterBody: (items) => {
                  const idx = items[0]?.dataIndex;
                  if (idx == null) return '';
                  const m = models[idx];
                  const total = m.inputTokens + m.outputTokens;
                  return `Total: ${total.toLocaleString()} tokens`;
                },
              },
            },
          },
          scales: {
            y: {
              stacked: true,
              beginAtZero: true,
              title: { display: true, text: 'Tokens', color: textDimColor, font: { size: 11 } },
              ticks: { color: textDimColor },
              grid: { color: gridColor },
            },
            x: {
              stacked: true,
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
                      const mult = tpd / baselineTPD;
                      lines.push(`${mult.toFixed(1)}x tokens/$ efficiency`);
                    }
                  }
                  if (m.durationMs > 0) {
                    lines.push(`${formatDuration(m.durationMs)}`);
                  }
                  return lines;
                },
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Cost (USD)', color: textDimColor, font: { size: 11 } },
              ticks: {
                color: textDimColor,
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
  }, [models, baseline]);

  const totalCost = models.reduce((sum, m) => sum + m.cost, 0);

  return (
    <div className="token-charts">
      <div className="token-charts-grid">
        <div className="token-chart-box">
          <div className="token-chart-title">Tokens by Model</div>
          <div className="token-chart-canvas"><canvas ref={tokenRef} /></div>
        </div>
        <div className="token-chart-box">
          <div className="token-chart-title">Cost by Model</div>
          <div className="token-chart-canvas"><canvas ref={costRef} /></div>
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
