import { useCallback, useEffect, useRef, useState, useMemo, type ReactNode } from 'react'
import { submitQueryStream, submitRating, fetchQueryHistory, fetchQueryDetail, evaluateQuery, refineQuery, applyRefinements, fetchGraphCapacity } from '../api'
import type { SlotSpec, GraphCapacity, StageEvent, ModelOption } from '../api'
import type { QueryResponse, QuerySummary, QueryDetail, SlotResult, EvalScoreOut, RefineResponse } from '../types'
import { useModels } from '../hooks/useModels'
import TokenCharts from './TokenCharts'
import SpreadTrail from './SpreadTrail'
import ChatNeuronViz from './ChatNeuronViz'
import { marked } from 'marked'

const layerColors = ['var(--layer0)', 'var(--layer1)', 'var(--layer2)', 'var(--layer3)', 'var(--layer4)', 'var(--layer5)'];

// Configure marked for LLM response rendering
marked.setOptions({ breaks: true, gfm: true });

// Provider color palette for dynamic mode coloring
const PROVIDER_COLORS: Record<string, [string, string]> = {
  google: ['#34d399', '#6ee7b7'],
  groq: ['#fbbf24', '#fcd34d'],
  anthropic: ['#60a5fa', '#a78bfa'],
};

function buildAllModes(models: ModelOption[]) {
  return models.flatMap(m => [
    { key: `${m.display_name}_neuron`, label: `${m.display_name} + Neurons`, short: m.display_name.slice(0, 3).toUpperCase() + 'N' },
    { key: `${m.display_name}_raw`, label: `${m.display_name} Raw`, short: m.display_name.slice(0, 3).toUpperCase() },
  ]);
}

function buildModeColors(models: ModelOption[]): Record<string, string> {
  const colors: Record<string, string> = {};
  for (const m of models) {
    const [neuronColor, rawColor] = PROVIDER_COLORS[m.provider] ?? ['#c8d0dc', '#d1d8e0'];
    colors[`${m.display_name}_neuron`] = neuronColor;
    colors[`${m.display_name}_raw`] = rawColor;
  }
  return colors;
}


// Module-level helpers for sub-components that can't access hook state
function getModeColor(mode: string, colorsOverride?: Record<string, string>): string {
  if (colorsOverride && colorsOverride[mode]) return colorsOverride[mode];
  // Derive a stable color from the mode name for unknown modes
  let hash = 0;
  for (let i = 0; i < mode.length; i++) hash = ((hash << 5) - hash + mode.charCodeAt(i)) | 0;
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 60%, 65%)`;
}

function getModeLabel(mode: string): string {
  // Derive human-readable label from mode key
  const [model, type] = mode.split('_');
  if (!type) return mode;
  return type === 'neuron' ? `${model} + Neurons` : `${model} Raw`;
}

// Generate distinct hex colors for same-mode slots at different budgets
// Must produce valid hex for Chart.js canvas (CSS color-mix doesn't work in canvas)
function slotColor(mode: string, index: number, total: number, colors: Record<string, string>): string {
  const base = colors[mode] ?? '#c8d0dc';
  if (total <= 1) return base;
  // Parse hex to RGB, shift lightness per index
  const r = parseInt(base.slice(1, 3), 16);
  const g = parseInt(base.slice(3, 5), 16);
  const b = parseInt(base.slice(5, 7), 16);
  const shift = -30 + (index * 30);
  const clamp = (v: number) => Math.max(0, Math.min(255, v + shift));
  return `#${clamp(r).toString(16).padStart(2, '0')}${clamp(g).toString(16).padStart(2, '0')}${clamp(b).toString(16).padStart(2, '0')}`;
}

function slotDisplayLabel(slot: SlotResult, allModes?: { key: string; label: string }[]): string {
  if (allModes) {
    const m = allModes.find(m => m.key === slot.mode);
    if (m) return m.label;
  }
  return getModeLabel(slot.mode);
}

function slotsToChartModels(slots: SlotResult[], classifyCost: number, baseline: string, colors?: Record<string, string>, allModes?: { key: string; label: string }[]) {
  const models = [];
  let firstNeuronDone = false;
  for (let i = 0; i < slots.length; i++) {
    const slot = slots[i];
    const isFirstNeuron = slot.neurons && !firstNeuronDone;
    if (isFirstNeuron) firstNeuronDone = true;
    // Count how many of this mode we've seen so far for color shifting
    const sameModeBefore = slots.slice(0, i).filter(s => s.mode === slot.mode).length;
    const sameModeTotal = slots.filter(s => s.mode === slot.mode).length;
    models.push({
      label: slotDisplayLabel(slot, allModes),
      mode: slot.mode,
      color: sameModeTotal > 1 ? slotColor(slot.mode, sameModeBefore, sameModeTotal, colors ?? {}) : getModeColor(slot.mode, colors),
      inputTokens: slot.input_tokens,
      outputTokens: slot.output_tokens,
      cost: slot.cost_usd + (isFirstNeuron ? classifyCost : 0),
      durationMs: slot.duration_ms ?? 0,
      neurons: slot.neurons,
      tokenBudget: slot.token_budget,
    });
  }
  return { models, baseline };
}

const DIMENSIONS = ['accuracy', 'completeness', 'clarity', 'faithfulness', 'overall'] as const;
const DIM_LABELS: Record<string, string> = { accuracy: 'Accuracy', completeness: 'Completeness', clarity: 'Clarity', faithfulness: 'Faithfulness', overall: 'Overall' };

function scoreColor(val: number): string {
  if (val >= 5) return '#22c55e';
  if (val >= 4) return '#86efac';
  if (val >= 3) return '#facc15';
  if (val >= 2) return '#fb923c';
  return '#ef4444';
}

function Section({ title, children, defaultOpen = false, className, headerRight, titleStyle, id }: {
  title: string; children: ReactNode; defaultOpen?: boolean; className?: string;
  headerRight?: ReactNode; titleStyle?: React.CSSProperties; id?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [read, setRead] = useState(defaultOpen);
  return (
    <div id={id} className={`result-card${className ? ' ' + className : ''}`}>
      <div className="section-header" onClick={() => { setOpen(o => !o); setRead(true); }}>
        <h3 style={titleStyle}>
          <span className={`section-chevron${open ? ' open' : ''}`} />
          {title}
          {!read && <span className="unread-dot" />}
        </h3>
        {headerRight && <div className="section-header-right" onClick={e => e.stopPropagation()}>{headerRight}</div>}
      </div>
      {open && children}
    </div>
  );
}

function EvalScoreTable({ scores, winner, slots }: { scores: EvalScoreOut[]; winner: string | null; slots?: SlotResult[] }) {
  if (scores.length === 0) return null;
  return (
    <div className="eval-score-table">
      <table className="score-table">
        <thead>
          <tr>
            <th>Dimension</th>
            {scores.map(s => {
              // Match by position (A=0, B=1, ...) not by mode, since multiple slots can share a mode
              const slotIndex = s.answer_label.charCodeAt(0) - 65;
              const matchedSlot = slots?.[slotIndex];
              const displayLabel = matchedSlot ? slotDisplayLabel(matchedSlot) : getModeLabel(s.answer_mode);
              return (
                <th key={s.answer_label} style={{ borderBottom: `2px solid ${getModeColor(s.answer_mode)}` }}>
                  {s.answer_label} — {displayLabel}
                  {winner === s.answer_label && <span style={{ marginLeft: 6, fontSize: '0.7rem', color: '#22c55e' }}>&#9733; Winner</span>}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {DIMENSIONS.map(dim => (
            <tr key={dim}>
              <td style={{ fontWeight: dim === 'overall' ? 700 : 400 }}>{DIM_LABELS[dim]}</td>
              {scores.map(s => {
                const val = s[dim];
                return (
                  <td key={s.answer_label} style={{ color: scoreColor(val), fontWeight: dim === 'overall' ? 700 : 400 }}>
                    {val}/5
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type RefinePhase = 'idle' | 'ready' | 'loading' | 'has-suggestions' | 'applying' | 'applied';

function RefinePanel({ queryId, hasEval, hasNeurons, onRunAgain, onPhaseChange, initialRefineResult, onNavigateToNeuron }: {
  queryId: number; hasEval: boolean; hasNeurons: boolean;
  onRunAgain?: () => void; onPhaseChange?: (phase: RefinePhase) => void;
  initialRefineResult?: RefineResponse | null;
  onNavigateToNeuron?: (id: number) => void;
}) {
  const { models: availableModels } = useModels();
  const [refineModel, setRefineModel] = useState<string>('haiku');
  const [refineMaxTokens, setRefineMaxTokens] = useState(4096);
  const [refineLoading, setRefineLoading] = useState(false);
  const [refineResult, setRefineResult] = useState<RefineResponse | null>(null);
  const [refineError, setRefineError] = useState('');
  const [checkedUpdates, setCheckedUpdates] = useState<Set<number>>(new Set());
  const [checkedNewNeurons, setCheckedNewNeurons] = useState<Set<number>>(new Set());
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyResult, setApplyResult] = useState<{ updated: number; created: number } | null>(null);
  const [userContext, setUserContext] = useState('');

  // Restore saved refine results (e.g. backend finished while user was on another tab)
  useEffect(() => {
    if (initialRefineResult && !refineResult && !refineLoading) {
      setRefineResult(initialRefineResult);
      setCheckedUpdates(new Set(initialRefineResult.updates.map((_, i) => i)));
      setCheckedNewNeurons(new Set(initialRefineResult.new_neurons.map((_, i) => i)));
    }
  }, [initialRefineResult]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!onPhaseChange || !hasEval || !hasNeurons) return;
    if (applyResult) onPhaseChange('applied');
    else if (applyLoading) onPhaseChange('applying');
    else if (refineResult && (refineResult.updates.length > 0 || refineResult.new_neurons.length > 0)) onPhaseChange('has-suggestions');
    else if (refineLoading) onPhaseChange('loading');
    else onPhaseChange('ready');
  }, [hasEval, hasNeurons, refineLoading, refineResult, applyLoading, applyResult, onPhaseChange]);

  if (!hasEval || !hasNeurons) return null;

  async function handleRefine() {
    setRefineLoading(true);
    setRefineError('');
    setApplyResult(null);
    try {
      const res = await refineQuery(queryId, refineModel, refineMaxTokens, userContext || undefined);
      setRefineResult(res);
      setCheckedUpdates(new Set(res.updates.map((_, i) => i)));
      setCheckedNewNeurons(new Set(res.new_neurons.map((_, i) => i)));
    } catch (e) {
      setRefineError(e instanceof Error ? e.message : 'Refinement failed');
    } finally {
      setRefineLoading(false);
    }
  }

  function toggleUpdate(idx: number) {
    setCheckedUpdates(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
  }

  function toggleNewNeuron(idx: number) {
    setCheckedNewNeurons(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
  }

  async function handleApply() {
    if (!refineResult) return;
    setApplyLoading(true);
    try {
      const res = await applyRefinements(queryId, Array.from(checkedUpdates), Array.from(checkedNewNeurons));
      setApplyResult(res);
    } catch (e) {
      setRefineError(e instanceof Error ? e.message : 'Apply failed');
    } finally {
      setApplyLoading(false);
    }
  }

  const totalChecked = checkedUpdates.size + checkedNewNeurons.size;

  return (
    <div id="section-refine" className="result-card refine-card">
      <div className="eval-header">
        <h3>Refine Neurons</h3>
        <div className="eval-controls">
          <select value={refineModel} onChange={e => setRefineModel(e.target.value)}>
            {availableModels.map(m => (
              <option key={m.display_name} value={m.display_name}>Refine with {m.display_name}</option>
            ))}
          </select>
          <label className="refine-token-slider">
            <span>Max tokens: {refineMaxTokens >= 1000 ? `${(refineMaxTokens / 1000).toFixed(1).replace(/\.0$/, '')}K` : refineMaxTokens}</span>
            <input
              type="range"
              min={512}
              max={16384}
              step={512}
              value={refineMaxTokens}
              onChange={e => setRefineMaxTokens(Number(e.target.value))}
            />
          </label>
          <button id="btn-refine" className="btn btn-sm" onClick={handleRefine} disabled={refineLoading}>
            {refineLoading ? 'Analyzing...' : refineResult ? 'Re-analyze' : 'Refine Neurons'}
          </button>
        </div>
      </div>

      <textarea
        className="refine-user-context"
        placeholder="Add your own context to guide refinement (e.g., specific standards, corrections, domain knowledge)..."
        value={userContext}
        onChange={e => setUserContext(e.target.value)}
        rows={3}
        style={{
          width: '100%',
          marginTop: 10,
          marginBottom: 10,
          resize: 'vertical',
          fontFamily: 'inherit',
          fontSize: '0.85rem',
          padding: '8px 10px',
          borderRadius: 6,
          border: '1px solid var(--border)',
          background: 'var(--bg-input, var(--bg-card))',
          color: 'var(--text)',
        }}
        maxLength={16000}
      />

      {refineError && <div className="error-msg" style={{ marginBottom: 12 }}>{refineError}</div>}

      {refineResult && (
        <div className="refine-results">
          <div className="refine-reasoning">
            <div className="eval-model-tag">Analysis by {refineResult.model}</div>
            <div className="response-text" style={{ marginBottom: 12 }}>{refineResult.reasoning}</div>
            <div className="token-breakdown">
              <div className="breakdown-item"><div className="bd-value">{refineResult.input_tokens}</div><div className="bd-label">In</div></div>
              <div className="breakdown-item"><div className="bd-value">{refineResult.output_tokens}</div><div className="bd-label">Out</div></div>
            </div>
          </div>

          {refineResult.updates.length > 0 && (
            <div className="refine-section">
              <h4>Neuron Updates ({refineResult.updates.length})</h4>
              {refineResult.updates.map((u, i) => (
                <label key={i} className={`refine-row${checkedUpdates.has(i) ? ' checked' : ''}`}>
                  <input type="checkbox" checked={checkedUpdates.has(i)} onChange={() => toggleUpdate(i)} />
                  <div className="refine-row-content">
                    <div className="refine-row-header">
                      <span className="refine-neuron-id" style={onNavigateToNeuron ? { cursor: 'pointer', textDecoration: 'underline' } : undefined} onClick={onNavigateToNeuron ? (e) => { e.preventDefault(); e.stopPropagation(); onNavigateToNeuron(u.neuron_id); } : undefined} title={onNavigateToNeuron ? 'View in Explorer' : undefined}>#{u.neuron_id}</span>
                      <span className="refine-field">{u.field}</span>
                    </div>
                    <div className="refine-diff">
                      <div className="refine-old">{u.old_value}</div>
                      <div className="refine-arrow">&rarr;</div>
                      <div className="refine-new">{u.new_value}</div>
                    </div>
                    <div className="refine-reason">{u.reason}</div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {refineResult.new_neurons.length > 0 && (
            <div className="refine-section">
              <h4>New Neurons ({refineResult.new_neurons.length})</h4>
              {refineResult.new_neurons.map((n, i) => (
                <label key={i} className={`refine-row${checkedNewNeurons.has(i) ? ' checked' : ''}`}>
                  <input type="checkbox" checked={checkedNewNeurons.has(i)} onChange={() => toggleNewNeuron(i)} />
                  <div className="refine-row-content">
                    <div className="refine-row-header">
                      <span className="refine-field">L{n.layer} {n.node_type}</span>
                      {n.parent_id != null && <span className="refine-neuron-id">under #{n.parent_id}</span>}
                      {n.department && <span className="tag dept" style={{ fontSize: '0.65rem' }}>{n.department}</span>}
                    </div>
                    <div className="refine-label">{n.label}</div>
                    <div className="refine-content-preview">{n.content.length > 200 ? n.content.slice(0, 200) + '...' : n.content}</div>
                    <div className="refine-reason">{n.reason}</div>
                  </div>
                </label>
              ))}
            </div>
          )}

          {(refineResult.updates.length > 0 || refineResult.new_neurons.length > 0) && (
            <div className="refine-apply-bar">
              {applyResult ? (
                <div className="refine-apply-success">
                  Applied: {applyResult.updated} updated, {applyResult.created} created
                  {onRunAgain && (
                    <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={onRunAgain}>
                      Run Again
                    </button>
                  )}
                </div>
              ) : (
                <button id="btn-apply" className="btn" onClick={handleApply} disabled={applyLoading || totalChecked === 0}>
                  {applyLoading ? 'Applying...' : `Apply Selected (${totalChecked})`}
                </button>
              )}
            </div>
          )}

          {refineResult.updates.length === 0 && refineResult.new_neurons.length === 0 && (
            <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginTop: 12 }}>
              No changes suggested — neurons look good for this query.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ────────── Unified Slot Builder ──────────

interface SlotConfig {
  id: number;
  mode: string;
  tokenBudget: number;
  topK: number;
  maxOutputTokens: number;
  color: string;
}

let nextSlotId = 1;

const TOKEN_MIN = 1000;
const TOKEN_MAX = 32000;
const TOPK_MIN = 1;
const TOPK_MAX = 500;
const OUTPUT_MIN = 512;
const OUTPUT_MAX = 8192;
const OUTPUT_Y_PCT = 90;
const PLOT_ASPECT = 2;

const SLOT_PALETTE = [
  '#60a5fa', '#34d399', '#f472b6', '#fbbf24', '#a78bfa',
  '#fb923c', '#22d3ee', '#e879f9', '#84cc16', '#f87171',
  '#2dd4bf', '#818cf8',
];
let nextSlotColorIdx = 0;
function nextSlotColor(): string {
  const c = SLOT_PALETTE[nextSlotColorIdx % SLOT_PALETTE.length];
  nextSlotColorIdx++;
  return c;
}

function UnifiedPlot({ slots, maxNeurons, selectedId, onSelect, onUpdateSlot }: {
  slots: SlotConfig[];
  maxNeurons: number;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onUpdateSlot: (id: number, patch: Partial<SlotConfig>) => void;
}) {
  const plotRef = useRef<HTMLDivElement>(null);
  const dragTarget = useRef<{ type: 'input' | 'output'; modelId: number } | null>(null);
  const neuronSlots = slots.filter(s => !s.mode.endsWith('_raw'));

  const effectiveTopKMax = Math.min(maxNeurons, TOPK_MAX);

  const yPctFromVal = useCallback((v: number) => {
    return (1 - (v - TOPK_MIN) / (effectiveTopKMax - TOPK_MIN)) * 100;
  }, [effectiveTopKMax]);

  const yValFromPct = useCallback((yPct: number) => {
    return Math.round(TOPK_MIN + (1 - yPct) * (effectiveTopKMax - TOPK_MIN));
  }, [effectiveTopKMax]);

  const xPctFromVal = useCallback((v: number) => {
    return ((v - TOKEN_MIN) / (TOKEN_MAX - TOKEN_MIN)) * 100;
  }, []);

  const xValFromPct = useCallback((xPct: number) => {
    return Math.round((TOKEN_MIN + xPct * (TOKEN_MAX - TOKEN_MIN)) / 1000) * 1000;
  }, []);

  const outputFromXPct = useCallback((xPct: number) => {
    const raw = TOKEN_MIN + xPct * (TOKEN_MAX - TOKEN_MIN);
    return Math.max(OUTPUT_MIN, Math.min(OUTPUT_MAX, Math.round(raw / 256) * 256));
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragTarget.current) return;
    const rect = plotRef.current!.getBoundingClientRect();
    const yPct = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    const xPct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const target = dragTarget.current;

    if (target.type === 'input') {
      const newTopK = Math.max(TOPK_MIN, Math.min(effectiveTopKMax, yValFromPct(yPct)));
      const newBudget = Math.max(TOKEN_MIN, Math.min(TOKEN_MAX, xValFromPct(xPct)));
      onUpdateSlot(target.modelId, { tokenBudget: newBudget, topK: newTopK });
    } else if (target.type === 'output') {
      const newOutput = outputFromXPct(xPct);
      onUpdateSlot(target.modelId, { maxOutputTokens: newOutput });
    }
  }, [effectiveTopKMax, yValFromPct, xValFromPct, outputFromXPct, onUpdateSlot]);

  // Find which slot a click is nearest to (for select or drag)
  const findNearest = useCallback((xPct: number, yPct: number) => {
    const GRAB_THRESH = 0.12;
    let closestDist = Infinity;
    let closestTarget: { type: 'input' | 'output'; modelId: number } | null = null;

    for (const s of neuronSlots) {
      const inputXPct = xPctFromVal(s.tokenBudget) / 100;
      const inputYPct = yPctFromVal(s.topK) / 100;
      const outputXPct = xPctFromVal(s.maxOutputTokens) / 100;
      const outputYPct = OUTPUT_Y_PCT / 100;

      const distToInput = Math.sqrt((xPct - inputXPct) ** 2 + (yPct - inputYPct) ** 2);
      const distToOutput = Math.sqrt((xPct - outputXPct) ** 2 + (yPct - outputYPct) ** 2);

      if (distToInput < closestDist && distToInput < GRAB_THRESH) {
        closestDist = distToInput;
        closestTarget = { type: 'input', modelId: s.id };
      }
      if (distToOutput < closestDist && distToOutput < GRAB_THRESH) {
        closestDist = distToOutput;
        closestTarget = { type: 'output', modelId: s.id };
      }
    }
    return closestTarget;
  }, [neuronSlots, yPctFromVal, xPctFromVal]);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    const rect = plotRef.current!.getBoundingClientRect();
    const xPct = (e.clientX - rect.left) / rect.width;
    const yPct = (e.clientY - rect.top) / rect.height;
    const nearest = findNearest(xPct, yPct);

    if (!nearest) {
      // Clicked empty space — deselect
      onSelect(null);
      return;
    }

    if (selectedId === nearest.modelId) {
      // Already selected — start dragging
      dragTarget.current = nearest;
      plotRef.current!.setPointerCapture(e.pointerId);
      handlePointerMove(e);
    } else {
      // Select this line
      onSelect(nearest.modelId);
    }
  }, [findNearest, selectedId, onSelect, handlePointerMove]);

  const onPointerUp = useCallback(() => {
    dragTarget.current = null;
  }, []);

  const xTicks = [1, 4, 8, 16, 32];
  const yTicks = [1, 10, 30, 50, 100, 250, 500].filter(v => v <= effectiveTopKMax);
  const hasSelection = selectedId != null;

  return (
    <div className="xy-plot-container">
      <div className="xy-plot-ylabel">Top-K</div>
      <div className="xy-plot-inner">
        <div className="xy-plot-yticks">
          {yTicks.map(v => {
            const top = yPctFromVal(v);
            return <span key={v} className="xy-tick-y" style={{ top: `${top}%` }}>{v}</span>;
          })}
        </div>
        <div
          ref={plotRef}
          className="xy-plot-area"
          style={{ aspectRatio: String(PLOT_ASPECT) }}
          onPointerDown={onPointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={onPointerUp}
        >
          {/* Grid lines */}
          {xTicks.map(v => {
            const left = xPctFromVal(v * 1000);
            return <div key={v} className="xy-gridline-v" style={{ left: `${left}%` }} />;
          })}
          {yTicks.map(v => {
            const top = yPctFromVal(v);
            return <div key={v} className="xy-gridline-h" style={{ top: `${top}%` }} />;
          })}

          {/* SVG lines */}
          <svg
            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            {neuronSlots.map(s => {
              const x1 = xPctFromVal(s.tokenBudget);
              const y1 = yPctFromVal(s.topK);
              const x2 = xPctFromVal(s.maxOutputTokens);
              const y2 = OUTPUT_Y_PCT;
              const isSelected = selectedId === s.id;
              const faded = hasSelection && !isSelected;
              return (
                <line key={s.id} x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={s.color}
                  strokeWidth={isSelected ? '1.2' : '0.6'}
                  strokeLinecap="round"
                  opacity={faded ? 0.2 : 1}
                />
              );
            })}
          </svg>

          {/* HTML dots and labels (neuron slots only) */}
          {neuronSlots.map(s => {
            const isSelected = selectedId === s.id;
            const faded = hasSelection && !isSelected;
            const outputXPct = xPctFromVal(s.maxOutputTokens);
            const inputXPct = xPctFromVal(s.tokenBudget);
            const inputYPct = yPctFromVal(s.topK);
            const dx = outputXPct - inputXPct;
            const dy = (OUTPUT_Y_PCT - inputYPct) / PLOT_ASPECT;
            let angleDeg = Math.atan2(dy, dx) * (180 / Math.PI);
            if (angleDeg > 90) angleDeg -= 180;
            if (angleDeg < -90) angleDeg += 180;
            const midXPct = (inputXPct + outputXPct) / 2;
            const midYPct = (inputYPct + OUTPUT_Y_PCT) / 2;
            const opacity = faded ? 0.2 : 1;

            return (
              <div key={s.id} style={{ opacity }}>
                <div className="uplot-dot" style={{
                  left: `${inputXPct}%`, top: `${inputYPct}%`,
                  background: s.color, borderColor: s.color,
                  width: isSelected ? 14 : 12, height: isSelected ? 14 : 12,
                  boxShadow: isSelected ? `0 0 10px ${s.color}` : undefined,
                }} />
                <div className="uplot-dot uplot-dot-sm" style={{
                  left: `${outputXPct}%`, top: `${OUTPUT_Y_PCT}%`,
                  background: s.color, borderColor: '#fff',
                  boxShadow: isSelected ? `0 0 10px ${s.color}` : undefined,
                }} />
                <div className="uplot-label" style={{
                  left: `${midXPct}%`, top: `${midYPct}%`,
                  color: s.color,
                  transform: `translate(-50%, -50%) rotate(${angleDeg}deg) translateY(-10px)`,
                }}>
                  {getModeLabel(s.mode)}
                </div>
              </div>
            );
          })}

          {/* Output Y level indicator */}
          <div className="xy-crosshair-h" style={{ top: `${OUTPUT_Y_PCT}%`, opacity: 0.15, borderTop: '1px dashed var(--text-dim)' }} />
          <div className="unified-output-label" style={{ top: `${OUTPUT_Y_PCT}%` }}>Output</div>

          {/* Readout */}
          <div className="xy-readout">
            {neuronSlots.map(s => <span key={s.id} style={{ color: s.color, opacity: hasSelection && selectedId !== s.id ? 0.3 : 1 }}>K={s.topK} </span>)}
          </div>
        </div>
        <div className="xy-plot-xticks">
          {xTicks.map(v => {
            const left = xPctFromVal(v * 1000);
            return <span key={v} className="xy-tick-x" style={{ left: `${left}%` }}>{v}K</span>;
          })}
        </div>
      </div>
      <div className="xy-plot-xlabel">Tokens (Input Budget &amp; Max Output)</div>
    </div>
  );
}

function SlotBuilder({ slots, onChange, capacity, groupedModels }: {
  slots: SlotConfig[];
  onChange: (slots: SlotConfig[]) => void;
  capacity: GraphCapacity | null;
  groupedModels: Record<string, ModelOption[]>;
}) {
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);
  const neuronSlots = slots.filter(s => !s.mode.endsWith('_raw'));
  const rawSlots = slots.filter(s => s.mode.endsWith('_raw'));

  function addSlot(mode: string) {
    onChange([...slots, { id: nextSlotId++, mode, tokenBudget: 8000, topK: 60, maxOutputTokens: 4096, color: nextSlotColor() }]);
  }

  function removeSlot(id: number) {
    if (selectedSlotId === id) setSelectedSlotId(null);
    onChange(slots.filter(s => s.id !== id));
  }

  function updateSlot(id: number, patch: Partial<SlotConfig>) {
    onChange(slots.map(s => s.id === id ? { ...s, ...patch } : s));
  }

  const maxNeurons = capacity?.active_neurons ?? 500;
  const hasSelection = selectedSlotId != null;

  return (
    <div className="slot-builder">
      {/* Auto-add dropdown */}
      <div className="unified-controls">
        <select
          className="qlt-mode-select"
          value=""
          onChange={e => { if (e.target.value) addSlot(e.target.value); }}
        >
          <option value="" disabled>Add model...</option>
          {Object.entries(groupedModels).map(([group, models]) => ([
            <option key={`hdr-${group}`} disabled>── {group} ──</option>,
            ...models.flatMap(m => [
              <option key={`${m.display_name}_neuron`} value={`${m.display_name}_neuron`}>{m.display_name} + Neurons</option>,
              <option key={`${m.display_name}_raw`} value={`${m.display_name}_raw`}>{m.display_name} Raw</option>,
            ]),
          ]))}
        </select>
      </div>

      {/* Model legend pills — click to select */}
      <div className="model-legend">
        {slots.map(s => {
          const isRaw = s.mode.endsWith('_raw');
          const isSelected = selectedSlotId === s.id;
          const faded = hasSelection && !isSelected;
          return (
            <span
              key={s.id}
              className={`model-pill${isSelected ? ' model-pill-selected' : ''}`}
              style={{ borderColor: s.color, color: s.color, opacity: faded ? 0.4 : 1, cursor: 'pointer' }}
              onClick={() => setSelectedSlotId(isSelected ? null : s.id)}
            >
              <span className="model-pill-dot" style={{ background: s.color }} />
              {getModeLabel(s.mode)}
              <span className="model-pill-detail">
                {isRaw ? `Out=${s.maxOutputTokens}` : `K=${s.topK} In=${Math.round(s.tokenBudget / 1000)}K Out=${s.maxOutputTokens}`}
              </span>
              <button className="model-pill-remove" onClick={e => { e.stopPropagation(); removeSlot(s.id); }} disabled={slots.length <= 1} title="Remove">&times;</button>
            </span>
          );
        })}
      </div>

      {capacity && (
        <div className="graph-capacity-bar">
          <span className="capacity-label">Graph:</span>
          <span className="capacity-value">{capacity.active_neurons.toLocaleString()} neurons</span>
          <span className="capacity-sep">&middot;</span>
          <span className="capacity-value">{capacity.total_content_tokens.toLocaleString()} content tokens</span>
          <span className="capacity-sep">&middot;</span>
          <span className="capacity-value">{capacity.total_tokens.toLocaleString()} total</span>
        </div>
      )}

      {/* Graph + raw models side by side */}
      <div className="unified-graph-row">
        <UnifiedPlot slots={neuronSlots} maxNeurons={maxNeurons} selectedId={selectedSlotId} onSelect={setSelectedSlotId} onUpdateSlot={updateSlot} />
        {rawSlots.length > 0 && (
          <div className="raw-models-column">
            <div className="raw-models-header">Raw</div>
            {rawSlots.map(s => (
              <div key={s.id} className="raw-model-chip" style={{ borderColor: s.color, color: s.color }}>
                <span className="model-pill-dot" style={{ background: s.color }} />
                {getModeLabel(s.mode)}
                <button className="model-pill-remove" onClick={() => removeSlot(s.id)} title="Remove">&times;</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ────────── Action Rail ──────────

const PIPELINE_LABELS = [
  { key: 'input_guard', label: 'Input Guard', section: 'section-guard' },
  { key: 'structural_resolve', label: 'Structural Resolve' },
  { key: 'embed_query', label: 'Embed Query' },
  { key: 'classify', label: 'Classify', section: 'section-classification' },
  { key: 'semantic_prefilter', label: 'Semantic Prefilter' },
  { key: 'score_neurons', label: 'Score Neurons', section: 'section-activations' },
  { key: 'spread_activation', label: 'Spread Activation', section: 'section-spread' },
  { key: 'assemble_prompt', label: 'Assemble Prompt' },
  { key: 'execute_llm', label: 'Execute LLM', section: 'section-slots' },
  { key: 'output_checks', label: 'Output Checks' },
];

function ActionRail({ result, hasMultiSlot, hasNeurons, evalDone, evalLoading, refinePhase, loading, stageStatuses, stageTimes, onEval, onSubmit }: {
  result: QueryResponse | null; hasMultiSlot: boolean; hasNeurons: boolean;
  evalDone: boolean; evalLoading: boolean; refinePhase: RefinePhase;
  loading: boolean; stageStatuses: Record<string, StageEvent>;
  stageTimes: Record<string, number>; // ms duration per stage
  onEval: () => void; onSubmit: () => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const hasResult = !!result;
  const active = loading || hasResult;

  function scrollAndClick(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.click();
    }
  }

  type StageStatus = 'pending' | 'active' | 'done' | 'skipped';

  function getStageStatus(key: string): StageStatus {
    if (!active) return 'pending';
    if (hasResult) {
      // Every stage that ran is 'done' — the stage completed its job regardless of outcome
      const ev = stageStatuses[key];
      if (ev) return 'done';
      return 'done'; // all stages complete when result exists
    }
    const ev = stageStatuses[key];
    if (ev) return ev.status === 'skipped' ? 'done' : ev.status as StageStatus;
    return 'pending';
  }

  function getStageDetail(key: string): string | undefined {
    const ev = stageStatuses[key];
    if (ev?.detail) {
      const d = ev.detail as Record<string, unknown>;
      if (d.intent) return String(d.intent);
      if (d.verdict) return String(d.verdict);
      if (d.candidates) return `${d.candidates} candidates`;
      if (d.scored) return `${d.scored} scored`;
      if (d.neurons_activated) return `${d.neurons_activated} neurons`;
    }
    if (hasResult) {
      if (key === 'classify' && result.intent) return result.intent;
      if (key === 'input_guard' && result.input_guard) return result.input_guard.verdict;
      if (key === 'assemble_prompt') return `${result.neurons_activated} neurons`;
      if (key === 'execute_llm' && result.slots.length > 0) return result.slots.map(s => s.model).join(', ');
    }
    return undefined;
  }

  // ── Workflow actions ──
  const workflowSteps = [
    {
      label: evalLoading ? 'Evaluating...' : evalDone ? 'Evaluated' : 'Evaluate',
      enabled: hasResult && hasMultiSlot && !evalLoading && !evalDone,
      done: evalDone,
      action: () => {
        document.getElementById('section-compare')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        onEval();
      },
    },
    {
      label: refinePhase === 'loading' ? 'Refining...' : refinePhase !== 'idle' && refinePhase !== 'ready' ? 'Refined' : 'Refine',
      enabled: evalDone && hasNeurons && (refinePhase === 'ready' || refinePhase === 'has-suggestions' || refinePhase === 'applied'),
      done: refinePhase === 'has-suggestions' || refinePhase === 'applying' || refinePhase === 'applied',
      action: () => scrollAndClick('btn-refine'),
    },
    {
      label: refinePhase === 'applying' ? 'Applying...' : refinePhase === 'applied' ? 'Applied' : 'Apply',
      enabled: refinePhase === 'has-suggestions',
      done: refinePhase === 'applied',
      action: () => scrollAndClick('btn-apply'),
    },
    {
      label: 'Run Again',
      enabled: refinePhase === 'applied',
      done: false,
      action: onSubmit,
    },
  ];

  return (
    <div className={`action-rail${collapsed ? ' collapsed' : ''}`}>
      <div className="rail-header" onClick={() => setCollapsed(c => !c)}>
        <span className={`section-chevron${!collapsed ? ' open' : ''}`} />
        {!collapsed && <span>Pipeline</span>}
      </div>
      {!collapsed && (
        <>
          <div className="rail-section-label">Stages</div>
          <div className="rail-steps">
            {PIPELINE_LABELS.map((stage, i) => {
              const status = getStageStatus(stage.key);
              const detail = getStageDetail(stage.key);
              const durationMs = stageTimes[stage.key];
              const isDone = status === 'done';
              const isActive = status === 'active';
              return (
                <button
                  key={stage.key}
                  className={`rail-step${isDone ? ' done' : ''}${isActive ? ' active' : ''}`}
                  disabled={!active}
                  onClick={() => stage.section && document.getElementById(stage.section)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                  style={{ cursor: stage.section && active ? 'pointer' : 'default' }}
                >
                  <span className="rail-step-num">
                    {isDone ? '\u2713' : isActive ? '\u25CF' : i + 1}
                  </span>
                  <div className="rail-step-content">
                    <span className="rail-step-label">{stage.label}</span>
                    {(detail || durationMs != null) && (
                      <span className="rail-step-meta">
                        {durationMs != null && <span className="rail-step-time">{durationMs < 1000 ? `${durationMs}ms` : `${(durationMs / 1000).toFixed(1)}s`}</span>}
                        {detail && <span className="rail-step-detail">{detail}</span>}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
          {hasResult && (
            <>
              <div className="rail-divider" />
              <div className="rail-section-label">Actions</div>
              <div className="rail-steps">
                {workflowSteps.map((step, i) => (
                  <button
                    key={i}
                    className={`rail-step${step.done ? ' done' : ''}`}
                    disabled={!step.enabled && !step.done}
                    onClick={step.action}
                  >
                    <span className="rail-step-num">{step.done ? '\u2713' : i + 1}</span>
                    <span className="rail-step-label">{step.label}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ────────── Main Component ──────────

export default function QueryLab({ onNavigateToNeuron }: { onNavigateToNeuron?: (id: number) => void } = {}) {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState('');
  const [rating, setRating] = useState(0.5);
  const [rated, setRated] = useState(false);

  const [elapsedMs, setElapsedMs] = useState(0);
  const elapsedRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { models: availableModels, grouped: groupedModels } = useModels();
  const ALL_MODES = useMemo(() => buildAllModes(availableModels), [availableModels]);
  const MODE_COLORS = useMemo(() => buildModeColors(availableModels), [availableModels]);


  const [slotConfigs, setSlotConfigs] = useState<SlotConfig[]>([
    { id: nextSlotId++, mode: 'haiku_neuron', tokenBudget: 8000, topK: 60, maxOutputTokens: 4096, color: nextSlotColor() },
  ]);
  const [baseline, setBaseline] = useState('opus_raw');
  const [graphCapacity, setGraphCapacity] = useState<GraphCapacity | null>(null);
  // Track which slot indices are still loading (for per-slot spinners)
  const [slotLoadingSet, setSlotLoadingSet] = useState<Set<number>>(new Set());

  const [evalLoading, setEvalLoading] = useState(false);
  const [evalModel, setEvalModel] = useState<string>('haiku');
  const [evalText, setEvalText] = useState<string | null>(null);
  const [evalMdl, setEvalMdl] = useState<string | null>(null);
  const [evalIn, setEvalIn] = useState(0);
  const [evalOut, setEvalOut] = useState(0);
  const [evalScores, setEvalScores] = useState<EvalScoreOut[]>([]);
  const [evalWinner, setEvalWinner] = useState<string | null>(null);
  const [evalLearning, setEvalLearning] = useState<import('../types').SynapticLearningOut | null>(null);

  const [history, setHistory] = useState<QuerySummary[]>([]);
  const [selectedQuery, setSelectedQuery] = useState<QueryDetail | null>(null);
  const [view, setView] = useState<'new' | 'history'>('new');

  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [refinePhase, setRefinePhase] = useState<RefinePhase>('idle');
  const [liveRefineRestore, setLiveRefineRestore] = useState<RefineResponse | null>(null);
  const [stageStatuses, setStageStatuses] = useState<Record<string, StageEvent>>({});
  const [stageTimes, setStageTimes] = useState<Record<string, number>>({});
  const stageTimestamps = useRef<Record<string, number>>({});
  const [configCollapsed, setConfigCollapsed] = useState(false);
  const abortRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    loadHistory();
    fetchGraphCapacity().then(setGraphCapacity).catch(() => {});
  }, []);

  // When returning to a live result, check if backend has saved refine results
  useEffect(() => {
    if (!result || refinePhase !== 'idle' || liveRefineRestore) return;
    fetchQueryDetail(result.query_id)
      .then(detail => {
        if (detail.pending_refine) setLiveRefineRestore(detail.pending_refine);
      })
      .catch(() => {});
  }, [result, refinePhase]); // eslint-disable-line react-hooks/exhaustive-deps

  function loadHistory() {
    fetchQueryHistory().then(setHistory).catch(() => {});
  }

  function buildSlotSpecs(): SlotSpec[] {
    return slotConfigs.map(sc => ({
      mode: sc.mode,
      token_budget: sc.tokenBudget,
      top_k: sc.topK,
      max_output_tokens: sc.maxOutputTokens,
    }));
  }

  async function handleSubmit() {
    const specs = buildSlotSpecs();
    if (!message.trim() || specs.length === 0) return;
    // Abort any in-flight stream
    if (abortRef.current) { abortRef.current(); abortRef.current = null; }
    setLoading(true);
    setError('');
    setResult(null);
    setEvalText(null);
    setEvalScores([]);
    setEvalWinner(null);
    setRated(false);
    setRefinePhase('idle');
    setLiveRefineRestore(null);
    setStageStatuses({});
    setStageTimes({});
    stageTimestamps.current = {};
    setConfigCollapsed(true);
    setView('new');
    setSelectedQuery(null);
    // Start elapsed timer
    const t0 = Date.now();
    elapsedRef.current = 0;
    setElapsedMs(0);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      elapsedRef.current = Date.now() - t0;
      setElapsedMs(elapsedRef.current);
    }, 100);
    // Mark all slots as loading
    setSlotLoadingSet(new Set(slotConfigs.map((_, i) => i)));
    // Add pending entry to history immediately
    const pendingEntry: QuerySummary = {
      id: -Date.now(),
      user_message: message,
      classified_intent: null,
      modes: specs.map(s => s.mode),
      cost_usd: null,
      user_rating: null,
      created_at: new Date().toISOString(),
    };
    setHistory(prev => [pendingEntry, ...prev]);
    try {
      const { promise, abort } = submitQueryStream(message, specs, (event) => {
        setStageStatuses(prev => ({ ...prev, [event.stage]: event }));
        // Track timing: duration = time since last stage event
        const now = Date.now();
        const keys = Object.keys(stageTimestamps.current);
        if (keys.length > 0) {
          const lastKey = keys[keys.length - 1];
          const lastTime = stageTimestamps.current[lastKey];
          setStageTimes(prev => ({ ...prev, [lastKey]: now - lastTime }));
        }
        stageTimestamps.current[event.stage] = now;
      });
      abortRef.current = abort;
      const res = await promise;
      // Capture final stage duration
      const finishTime = Date.now();
      const keys = Object.keys(stageTimestamps.current);
      if (keys.length > 0) {
        const lastKey = keys[keys.length - 1];
        setStageTimes(prev => ({ ...prev, [lastKey]: finishTime - stageTimestamps.current[lastKey] }));
      }
      setResult(res);
      loadHistory();
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        setError(e instanceof Error ? e.message : 'Query failed');
      }
    } finally {
      abortRef.current = null;
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      setElapsedMs(elapsedRef.current); // freeze final value
      setLoading(false);
      setSlotLoadingSet(new Set());
    }
  }

  function handleNewQuery() {
    setMessage('');
    setResult(null);
    setEvalText(null);
    setEvalScores([]);
    setEvalWinner(null);
    setRated(false);
    setRefinePhase('idle');
    setLiveRefineRestore(null);
    setStageStatuses({});
    setStageTimes({});
    stageTimestamps.current = {};
    setConfigCollapsed(false);
    setError('');
    setView('new');
    setSelectedQuery(null);
    document.querySelector('.query-form')?.scrollIntoView({ behavior: 'smooth' });
  }

  function handleRunAgain() {
    setResult(null);
    setEvalText(null);
    setEvalScores([]);
    setEvalWinner(null);
    setRated(false);
    setRefinePhase('idle');
    setLiveRefineRestore(null);
    setStageStatuses({});
    setStageTimes({});
    stageTimestamps.current = {};
    setView('new');
    setSelectedQuery(null);
    document.querySelector('.query-form')?.scrollIntoView({ behavior: 'smooth' });
  }

  async function handleEval() {
    if (!result) return;
    setEvalLoading(true);
    try {
      const res = await evaluateQuery(result.query_id, evalModel);
      setEvalText(res.eval_text);
      setEvalMdl(res.eval_model);
      setEvalIn(res.eval_input_tokens);
      setEvalOut(res.eval_output_tokens);
      setEvalScores(res.scores ?? []);
      setEvalWinner(res.winner ?? null);
      setEvalLearning(res.learning ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evaluation failed');
    } finally {
      setEvalLoading(false);
    }
  }

  async function handleRate() {
    if (!result) return;
    try {
      await submitRating(result.query_id, rating);
      setRated(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rating failed');
    }
  }

  async function selectHistoryItem(id: number) {
    try {
      const detail = await fetchQueryDetail(id);
      setSelectedQuery(detail);
      setView('history');
      setResult(null);
      setEvalText(null);
      setRefinePhase('idle');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load query');
    }
  }

  const hasResult = !!result && view === 'new';
  const hasNeurons = hasResult && result.neuron_scores.length > 0;
  const hasMultiSlot = hasResult && result.slots.length >= 2;

  return (
    <div className="query-lab-layout">
      <div className={`query-history${historyCollapsed ? ' collapsed' : ''}`}>
        <h3 style={{ display: 'flex', alignItems: 'flex-end', gap: 6, paddingBottom: 6 }}>
          <span onClick={() => setHistoryCollapsed(c => !c)} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
            <span className="sidebar-toggle" style={{ padding: 2 }}>{historyCollapsed ? '\u25B6' : '\u25C0'}</span>
            {!historyCollapsed ? 'Query History' : ''}
          </span>
          {!historyCollapsed && (
            <button
              className="btn btn-sm"
              title="New query"
              style={{ padding: '2px 7px', fontSize: '0.85rem', lineHeight: 1 }}
              onClick={handleNewQuery}
            >+</button>
          )}
        </h3>
        {!historyCollapsed && (
          <>
            {history.length === 0 && <div className="history-empty">No queries yet</div>}
            {history.map(q => {
              const isPending = q.id < 0;
              return (
                <div
                  key={q.id}
                  className={`history-item${selectedQuery?.id === q.id ? ' selected' : ''}${isPending ? ' pending' : ''}`}
                  onClick={() => !isPending && selectHistoryItem(q.id)}
                  style={isPending ? { cursor: 'default' } : undefined}
                >
                  <div className="history-header-row">
                    <span className="history-id">#{q.id}</span>
                    {q.cost_usd != null && <span className="history-cost">${q.cost_usd.toFixed(4)}</span>}
                  </div>
                  <div className="history-msg">{q.user_message}</div>
                  <div className="history-meta">
                    {isPending && <span className="tag intent" style={{ opacity: 0.7 }}>Running...</span>}
                    {!isPending && q.classified_intent && <span className="tag intent">{q.classified_intent}</span>}
                    <span className="history-modes">
                      {q.modes.map(m => {
                        const def = ALL_MODES.find(d => d.key === m);
                        return <span key={m} className="mode-badge" style={{ background: (MODE_COLORS[m] ?? '#c8d0dc') + '33', color: MODE_COLORS[m] ?? '#c8d0dc' }}>{def?.short ?? m}</span>;
                      })}
                    </span>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>

      <div className="query-main">
        <div className="query-form">
          <textarea
            placeholder="Enter your message..."
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) handleSubmit(); }}
          />
          <div className={`query-controls${configCollapsed ? ' config-collapsed' : ''}`}>
            <div className="config-collapse-toggle" onClick={() => setConfigCollapsed(c => !c)}>
              <span className={`section-chevron${!configCollapsed ? ' open' : ''}`} />
              <span>{configCollapsed ? 'Show model config' : 'Model config'}</span>
            </div>
            <div className="config-collapsible">
              <SlotBuilder slots={slotConfigs} onChange={setSlotConfigs} capacity={graphCapacity} groupedModels={groupedModels} />
              <div className="query-controls-bottom">
                <select className="baseline-select" value={baseline} onChange={e => setBaseline(e.target.value)}>
                  {Object.entries(groupedModels).map(([group, models]) => (
                    [
                      <option key={`bl-hdr-${group}`} disabled>── {group} ──</option>,
                      ...models.flatMap(m => [
                        <option key={`${m.display_name}_neuron`} value={`${m.display_name}_neuron`}>Baseline: {m.display_name} + Neurons</option>,
                        <option key={`${m.display_name}_raw`} value={`${m.display_name}_raw`}>Baseline: {m.display_name} Raw</option>,
                      ]),
                    ]
                  ))}
                </select>
                <button className="btn" onClick={handleSubmit} disabled={loading || !message.trim() || slotConfigs.length === 0}>
                  {loading ? 'Processing...' : `Submit (${slotConfigs.length} slot${slotConfigs.length !== 1 ? 's' : ''})`}
                </button>
              </div>
            </div>
          </div>
        </div>

        {error && <div className="error-msg">{error}</div>}

        {/* Per-slot loading indicators */}
        {loading && (
          <div className="slot-loading-panel">
            <div className="slot-loading-timer">{(elapsedMs / 1000).toFixed(1)}s</div>
            {slotConfigs.map((sc, i) => {
              const modeInfo = ALL_MODES.find(m => m.key === sc.mode);
              const label = modeInfo?.label ?? sc.mode;
              const done = !slotLoadingSet.has(i);
              return (
                <div key={sc.id} className={`slot-loading-item${done ? ' done' : ''}`}>
                  {!done && <span className="slot-spinner" />}
                  {done && <span className="slot-check">&#10003;</span>}
                  <span className="slot-loading-label" style={{ color: sc.color }}>{label}</span>
                </div>
              );
            })}
          </div>
        )}

        {result && view === 'new' && (
          <LiveResult
            result={result} baseline={baseline}
            totalElapsedMs={elapsedMs}
            rating={rating} setRating={setRating} rated={rated} onRate={handleRate}
            evalText={evalText} evalMdl={evalMdl} evalIn={evalIn} evalOut={evalOut}
            evalScores={evalScores} evalWinner={evalWinner}
            evalLearning={evalLearning}
            evalModel={evalModel} setEvalModel={setEvalModel}
            evalLoading={evalLoading} onEval={handleEval}
            onRunAgain={handleRunAgain} onRefinePhaseChange={setRefinePhase}
            initialRefineResult={liveRefineRestore}
            onNavigateToNeuron={onNavigateToNeuron}
          />
        )}

        {selectedQuery && view === 'history' && <HistoryDetail query={selectedQuery} baseline={baseline} onNavigateToNeuron={onNavigateToNeuron} />}
      </div>

      <ActionRail
        result={result}
        hasMultiSlot={hasMultiSlot}
        hasNeurons={hasNeurons}
        evalDone={!!evalText}
        evalLoading={evalLoading}
        refinePhase={refinePhase}
        loading={loading}
        stageStatuses={stageStatuses}
        stageTimes={stageTimes}
        onEval={handleEval}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

// ────────── Live Result ──────────

function LiveResult({ result, baseline, totalElapsedMs, rating, setRating, rated, onRate, evalText, evalMdl, evalIn, evalOut, evalScores, evalWinner, evalLearning, evalModel, setEvalModel, evalLoading, onEval, onRunAgain, onRefinePhaseChange, initialRefineResult, onNavigateToNeuron }: {
  result: QueryResponse; baseline: string; totalElapsedMs?: number;
  rating: number; setRating: (v: number) => void; rated: boolean; onRate: () => void;
  evalText: string | null; evalMdl: string | null; evalIn: number; evalOut: number;
  evalScores: EvalScoreOut[]; evalWinner: string | null;
  evalLearning: import('../types').SynapticLearningOut | null;
  evalModel: string; setEvalModel: (v: string) => void;
  evalLoading: boolean; onEval: () => void;
  onRunAgain: () => void; onRefinePhaseChange: (phase: RefinePhase) => void;
  initialRefineResult?: RefineResponse | null;
  onNavigateToNeuron?: (id: number) => void;
}) {
  const hasNeurons = result.neuron_scores.length > 0;
  const { models: availableModels } = useModels();

  return (
    <>
      {hasNeurons && (
        <ChatNeuronViz
          queryId={result.query_id}
          neuronScores={result.neuron_scores}
          neuronsActivated={result.neurons_activated}
          onNavigateToNeuron={onNavigateToNeuron}
          fullSize
        />
      )}

      {hasNeurons && result.intent && (
        <Section title="Classification" defaultOpen={false}>
          <div className="tags">
            <span className="tag intent">{result.intent}</span>
            {result.departments.map(d => <span key={d} className="tag dept">{d}</span>)}
            {result.role_keys.map(r => <span key={r} className="tag role">{r}</span>)}
            {result.keywords.map(k => <span key={k} className="tag keyword">{k}</span>)}
          </div>
        </Section>
      )}

      {/* Input Guard */}
      {result.input_guard && result.input_guard.flag_count > 0 && (
        <div style={{
          padding: '8px 12px', marginBottom: 12, borderRadius: 6, fontSize: '0.8rem',
          background: result.input_guard.verdict === 'warn' ? '#fb923c18' : '#ef444418',
          border: `1px solid ${result.input_guard.verdict === 'warn' ? '#fb923c44' : '#ef444444'}`,
        }}>
          <div style={{ fontWeight: 600, marginBottom: 4, color: result.input_guard.verdict === 'warn' ? '#fb923c' : '#ef4444' }}>
            Input Guard: {result.input_guard.verdict.toUpperCase()} ({result.input_guard.flag_count} flag{result.input_guard.flag_count !== 1 ? 's' : ''})
          </div>
          {result.input_guard.flags.map((f, i) => (
            <div key={i} style={{ color: 'var(--text-dim)' }}>
              <span style={{ color: f.severity === 'warn' ? '#fb923c' : '#ef4444', fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase' }}>{f.severity}</span>
              {' '}{f.description}{f.pattern ? ` — "${f.pattern}"` : ''}
            </div>
          ))}
        </div>
      )}

      {/* Responses with output checks */}
      {result.slots.map((slot, i) => {
        const check = result.output_checks?.[i];
        return (
          <Section key={i} title={slotDisplayLabel(slot)} titleStyle={{ borderLeft: `3px solid ${getModeColor(slot.mode)}`, paddingLeft: 8 }}>
            {check && (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                {check.grounding && check.grounding.confidence !== null && (
                  <span style={{
                    fontSize: '0.65rem', padding: '1px 6px', borderRadius: 3, fontFamily: 'var(--font-mono, monospace)',
                    background: check.grounding.grounded ? '#22c55e22' : '#fb923c22',
                    color: check.grounding.grounded ? '#22c55e' : '#fb923c',
                    border: `1px solid ${check.grounding.grounded ? '#22c55e44' : '#fb923c44'}`,
                  }} title={check.grounding.reason}>
                    Grounding: {(check.grounding.confidence * 100).toFixed(0)}%
                    {check.grounding.ungrounded_references && check.grounding.ungrounded_references.length > 0 &&
                      ` (${check.grounding.ungrounded_references.length} unverified ref${check.grounding.ungrounded_references.length !== 1 ? 's' : ''})`
                    }
                  </span>
                )}
                {check.risk_flags.map((rf, j) => (
                  <span key={j} style={{
                    fontSize: '0.65rem', padding: '1px 6px', borderRadius: 3, fontFamily: 'var(--font-mono, monospace)',
                    background: rf.category === 'dual_use' ? '#ef444422' : rf.category === 'safety_critical' ? '#fb923c22' : '#3b82f622',
                    color: rf.category === 'dual_use' ? '#ef4444' : rf.category === 'safety_critical' ? '#fb923c' : '#3b82f6',
                    border: `1px solid ${rf.category === 'dual_use' ? '#ef444444' : rf.category === 'safety_critical' ? '#fb923c44' : '#3b82f644'}`,
                  }} title={rf.excerpt}>
                    {rf.category}: {rf.description}
                  </span>
                ))}
              </div>
            )}
            {slot.error ? (
              <div style={{ padding: '12px 16px', background: '#ef444422', border: '1px solid #ef444444', borderRadius: 6, color: '#fca5a5', fontSize: '0.85rem' }}>
                {slot.response}
              </div>
            ) : (
              <div className="response-text markdown-body" dangerouslySetInnerHTML={{ __html: marked.parse(slot.response ?? '', { async: false }) as string }} />
            )}
          </Section>
        );
      })}

      {/* Token Charts */}
      <Section title="Cost & Tokens">
        <TokenCharts {...slotsToChartModels(result.slots, result.classify_cost, baseline)} totalElapsedMs={totalElapsedMs} />
      </Section>

      {/* Compare */}
      {result.slots.length >= 2 && (
        <Section id="section-compare" title="Compare Outputs" className="eval-card" headerRight={
          <div className="eval-controls">
            <select value={evalModel} onChange={e => setEvalModel(e.target.value)}>
              {availableModels.map(m => (
                <option key={m.display_name} value={m.display_name}>Evaluate with {m.display_name}</option>
              ))}
            </select>
            <button className="btn btn-sm" onClick={onEval} disabled={evalLoading || !!evalText}>
              {evalLoading ? 'Evaluating...' : evalText ? 'Evaluated' : 'Compare Outputs'}
            </button>
          </div>
        }>
          {evalText && (
            <div className="eval-result">
              <div className="eval-model-tag">Evaluated by {evalMdl}</div>
              <EvalScoreTable scores={evalScores} winner={evalWinner} slots={result.slots} />
              <div className="response-text" style={{ marginTop: 12 }}>{evalText}</div>
              <div className="token-breakdown" style={{ marginTop: 12 }}>
                <div className="breakdown-item"><div className="bd-value">{evalIn}</div><div className="bd-label">Eval In</div></div>
                <div className="breakdown-item"><div className="bd-value">{evalOut}</div><div className="bd-label">Eval Out</div></div>
              </div>
              {evalLearning && evalLearning.outcome !== 'skip' && (
                <div style={{
                  marginTop: 14, padding: '10px 14px', borderRadius: 6,
                  background: evalLearning.outcome === 'win' ? '#22c55e15' : evalLearning.outcome === 'loss' ? '#ef444415' : '#fbbf2415',
                  border: `1px solid ${evalLearning.outcome === 'win' ? '#22c55e33' : evalLearning.outcome === 'loss' ? '#ef444433' : '#fbbf2433'}`,
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: evalLearning.outcome === 'win' ? '#22c55e' : evalLearning.outcome === 'loss' ? '#ef4444' : '#fbbf24', marginBottom: 4 }}>
                    Synaptic Learning: {evalLearning.outcome.toUpperCase()}
                    {evalLearning.winner_mode && <span style={{ fontWeight: 400, opacity: 0.7 }}> ({evalLearning.winner_mode})</span>}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'flex', gap: 16 }}>
                    <span>{evalLearning.neurons_adjusted} neurons adjusted</span>
                    <span>avg delta: {evalLearning.avg_delta >= 0 ? '+' : ''}{evalLearning.avg_delta.toFixed(4)}</span>
                    {evalLearning.edges_adjusted > 0 && <span>{evalLearning.edges_adjusted} edges accelerated</span>}
                  </div>
                </div>
              )}
            </div>
          )}
        </Section>
      )}

      <RefinePanel queryId={result.query_id} hasEval={!!evalText} hasNeurons={hasNeurons} onRunAgain={onRunAgain} onPhaseChange={onRefinePhaseChange} initialRefineResult={initialRefineResult} onNavigateToNeuron={onNavigateToNeuron} />

      {result.slots.length >= 1 && (
        <Section title="Export for External Review">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: 12 }}>
            Download a blind evaluation file for an external model (e.g., ChatGPT). Answers are labeled A/B/C with no model identification.
          </p>
          <button className="btn btn-sm" onClick={() => {
            const lines: string[] = [];
            lines.push('='.repeat(80));
            lines.push('BLIND EVALUATION REQUEST');
            lines.push('='.repeat(80));
            lines.push('');
            lines.push('You are evaluating multiple AI-generated answers to the same prompt.');
            lines.push('Each answer is labeled with a letter (A, B, C, etc.). You do not know');
            lines.push('which model produced which answer.');
            lines.push('');
            lines.push('Score each answer on the following dimensions (1-5 scale):');
            lines.push('');
            lines.push('  Accuracy      - Are the facts, standards, and procedures correct?');
            lines.push('  Completeness  - Does it cover all relevant aspects of the question?');
            lines.push('  Clarity       - Is it well-organized and easy to follow?');
            lines.push('  Faithfulness  - Does it avoid hallucinated facts or made-up references?');
            lines.push('  Overall       - Holistic quality considering all dimensions above.');
            lines.push('');
            lines.push('After scoring, select a winner (the best overall answer).');
            lines.push('Provide a brief justification for your scores and winner selection.');
            lines.push('');
            lines.push('='.repeat(80));
            lines.push('PROMPT');
            lines.push('='.repeat(80));
            lines.push('');
            lines.push(`User query: ${baseline}`);
            lines.push('');

            result.slots.forEach((slot, i) => {
              const label = String.fromCharCode(65 + i);
              lines.push('='.repeat(80));
              lines.push(`ANSWER ${label}`);
              lines.push('='.repeat(80));
              lines.push('');
              lines.push(slot.response);
              lines.push('');
            });

            if (evalScores.length > 0) {
              lines.push('='.repeat(80));
              lines.push('INTERNAL EVALUATION (for comparison — do not let this bias your scoring)');
              lines.push('='.repeat(80));
              lines.push('');
              lines.push('Dimension'.padEnd(16) + evalScores.map(s => `Answer ${s.answer_label}`.padEnd(12)).join(''));
              lines.push('-'.repeat(16 + evalScores.length * 12));
              for (const dim of ['accuracy', 'completeness', 'clarity', 'faithfulness', 'overall'] as const) {
                const label = dim.charAt(0).toUpperCase() + dim.slice(1);
                lines.push(label.padEnd(16) + evalScores.map(s => `${s[dim]}/5`.padEnd(12)).join(''));
              }
              lines.push('');
              if (evalWinner) {
                lines.push(`Internal winner: Answer ${evalWinner}`);
              }
              if (evalText) {
                lines.push('');
                lines.push('Internal verdict:');
                lines.push(evalText);
              }
            }

            lines.push('');
            lines.push('='.repeat(80));
            lines.push('END OF EVALUATION FILE');
            lines.push('='.repeat(80));

            const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `corvus-blind-eval-q${result.query_id}.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }}>
            Export Blind Evaluation (.txt)
          </button>
        </Section>
      )}

      <Section title="Rate Response">
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <button
            className="btn btn-sm"
            style={{ fontSize: '1.1rem', padding: '4px 12px', background: rated && rating >= 0.7 ? '#22c55e33' : undefined, border: rated && rating >= 0.7 ? '1px solid #22c55e' : undefined }}
            onClick={() => { setRating(0.85); }}
            disabled={rated}
            title="Good response (0.85)"
          >
            {'👍'}
          </button>
          <button
            className="btn btn-sm"
            style={{ fontSize: '1.1rem', padding: '4px 12px', background: rated && rating < 0.3 ? '#ef444433' : undefined, border: rated && rating < 0.3 ? '1px solid #ef4444' : undefined }}
            onClick={() => { setRating(0.15); }}
            disabled={rated}
            title="Poor response (0.15)"
          >
            {'👎'}
          </button>
          <button className="btn btn-sm" onClick={onRate} disabled={rated} style={{ marginLeft: 'auto' }}>{rated ? 'Rated!' : 'Submit Rating'}</button>
        </div>
        <div className="rating-row">
          <input type="range" min="0" max="1" step="0.05" value={rating} onChange={e => setRating(parseFloat(e.target.value))} disabled={rated} />
          <span className="rating-value">{rating.toFixed(2)}</span>
        </div>
      </Section>
    </>
  );
}

// ────────── History Detail ──────────

function HistoryDetail({ query, baseline, onNavigateToNeuron }: { query: QueryDetail; baseline: string; onNavigateToNeuron?: (id: number) => void }) {
  const { models: availableModels } = useModels();
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalModel, setEvalModel] = useState<string>('haiku');
  const [localEvalText, setLocalEvalText] = useState(query.eval_text);
  const [localEvalMdl, setLocalEvalMdl] = useState(query.eval_model);
  const [localEvalIn, setLocalEvalIn] = useState(query.eval_input_tokens);
  const [localEvalOut, setLocalEvalOut] = useState(query.eval_output_tokens);
  const [localEvalScores, setLocalEvalScores] = useState<EvalScoreOut[]>(query.eval_scores ?? []);
  const [localEvalWinner, setLocalEvalWinner] = useState<string | null>(query.eval_winner ?? null);

  useEffect(() => {
    setLocalEvalText(query.eval_text);
    setLocalEvalMdl(query.eval_model);
    setLocalEvalIn(query.eval_input_tokens);
    setLocalEvalOut(query.eval_output_tokens);
    setLocalEvalScores(query.eval_scores ?? []);
    setLocalEvalWinner(query.eval_winner ?? null);
  }, [query]);

  async function handleEval() {
    setEvalLoading(true);
    try {
      const res = await evaluateQuery(query.id, evalModel);
      setLocalEvalText(res.eval_text);
      setLocalEvalMdl(res.eval_model);
      setLocalEvalIn(res.eval_input_tokens);
      setLocalEvalOut(res.eval_output_tokens);
      setLocalEvalScores(res.scores ?? []);
      setLocalEvalWinner(res.winner ?? null);
    } catch { /* ignore */ }
    finally { setEvalLoading(false); }
  }

  const hasNeurons = query.neuron_hits.length > 0;

  return (
    <>
      <div className="result-card">
        <h3>
          Query #{query.id}
          <span className="history-modes" style={{ marginLeft: 8 }}>
            {query.slots.map((s, i) => {
              const label = slotDisplayLabel(s);
              return <span key={i} className="mode-badge" style={{ background: (getModeColor(s.mode)) + '33', color: getModeColor(s.mode) }}>{label}</span>;
            })}
          </span>
        </h3>
        <div className="response-text" style={{ marginBottom: 12, position: 'relative' }}>
          {query.user_message}
          <button
            className="copy-btn"
            title="Copy prompt"
            onClick={() => {
              navigator.clipboard.writeText(query.user_message);
            }}
          >
            Copy
          </button>
        </div>
        {hasNeurons && (
          <div className="tags">
            {query.classified_intent && <span className="tag intent">{query.classified_intent}</span>}
            {query.departments.map(d => <span key={d} className="tag dept">{d}</span>)}
            {query.role_keys.map(r => <span key={r} className="tag role">{r}</span>)}
            {query.keywords.map(k => <span key={k} className="tag keyword">{k}</span>)}
          </div>
        )}
        {query.created_at && <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 8 }}>{new Date(query.created_at).toLocaleString()}</div>}
      </div>

      {hasNeurons && (
        <Section title={`Neuron Hits (${query.neuron_hits.length} neurons activated)`} defaultOpen={false}>
          <table className="score-table">
            <thead>
              <tr><th>ID</th><th>Neuron</th><th>Layer</th><th>Dept</th><th>Combined</th><th>Spread</th><th>Burst</th><th>Impact</th><th>Precision</th><th>Novelty</th><th>Recency</th><th>Relevance</th></tr>
            </thead>
            <tbody>
              {query.neuron_hits.map(h => (
                <tr key={h.neuron_id}>
                  <td>{h.neuron_id}</td>
                  <td style={{ color: layerColors[h.layer], maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.label}</td>
                  <td><span style={{ color: layerColors[h.layer] }}>L{h.layer}</span></td>
                  <td style={{ fontSize: '0.75rem' }}>{h.department ?? '—'}</td>
                  <td><strong>{h.combined.toFixed(3)}</strong></td>
                  <td style={h.spread_boost > 0 ? { color: '#e8a735', fontWeight: 600 } : undefined}>{h.spread_boost > 0 ? h.spread_boost.toFixed(3) : '—'}</td>
                  <td>{h.burst.toFixed(3)}</td>
                  <td>{h.impact.toFixed(3)}</td>
                  <td>{h.precision.toFixed(3)}</td>
                  <td>{h.novelty.toFixed(3)}</td>
                  <td>{h.recency.toFixed(3)}</td>
                  <td>{h.relevance.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {query.neuron_hits.length > 0 && (
        <Section title="Activation Graph" defaultOpen={false}>
          <SpreadTrail queryId={query.id} neuronScores={query.neuron_hits.map(h => ({
            neuron_id: h.neuron_id, combined: h.combined, burst: h.burst,
            impact: h.impact, precision: h.precision, novelty: h.novelty,
            recency: h.recency, relevance: h.relevance, spread_boost: h.spread_boost,
            label: h.label, department: h.department, layer: h.layer,
            parent_id: h.parent_id, summary: h.summary,
          }))} onNavigateToNeuron={onNavigateToNeuron} />
        </Section>
      )}

      {/* Responses */}
      {query.slots.map((slot, i) => (
        <Section key={i} title={slotDisplayLabel(slot)} titleStyle={{ borderLeft: `3px solid ${getModeColor(slot.mode)}`, paddingLeft: 8 }}>
          {slot.error ? (
            <div style={{ padding: '12px 16px', background: '#ef444422', border: '1px solid #ef444444', borderRadius: 6, color: '#fca5a5', fontSize: '0.85rem' }}>
              {slot.response}
            </div>
          ) : (
            <div className="response-text">{slot.response}</div>
          )}
        </Section>
      ))}

      {/* Token Charts */}
      {query.slots.length > 0 && (
        <Section title="Cost & Tokens">
          <TokenCharts {...slotsToChartModels(query.slots, query.classify_cost, baseline)} />
        </Section>
      )}

      {/* Compare */}
      {query.slots.length >= 2 && (
        <Section title="Compare Outputs" className="eval-card" headerRight={
          <div className="eval-controls">
            <select value={evalModel} onChange={e => setEvalModel(e.target.value)}>
              {availableModels.map(m => (
                <option key={m.display_name} value={m.display_name}>Evaluate with {m.display_name}</option>
              ))}
            </select>
            <button className="btn btn-sm" onClick={handleEval} disabled={evalLoading}>
              {evalLoading ? 'Evaluating...' : localEvalText ? 'Re-evaluate' : 'Compare Outputs'}
            </button>
          </div>
        }>
          {localEvalText && (
            <div className="eval-result">
              <div className="eval-model-tag">Evaluated by {localEvalMdl}</div>
              <EvalScoreTable scores={localEvalScores} winner={localEvalWinner} slots={query.slots} />
              <div className="response-text" style={{ marginTop: 12 }}>{localEvalText}</div>
              <div className="token-breakdown" style={{ marginTop: 12 }}>
                <div className="breakdown-item"><div className="bd-value">{localEvalIn}</div><div className="bd-label">Eval In</div></div>
                <div className="breakdown-item"><div className="bd-value">{localEvalOut}</div><div className="bd-label">Eval Out</div></div>
              </div>
            </div>
          )}
        </Section>
      )}

      {query.slots.length >= 1 && (
        <Section title="Export for External Review">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: 12 }}>
            Download a blind evaluation file for an external model (e.g., ChatGPT). Answers are labeled A/B/C with no model identification.
          </p>
          <button className="btn btn-sm" onClick={() => {
            const lines: string[] = [];
            lines.push('='.repeat(80));
            lines.push('BLIND EVALUATION REQUEST');
            lines.push('='.repeat(80));
            lines.push('');
            lines.push('You are evaluating multiple AI-generated answers to the same prompt.');
            lines.push('Each answer is labeled with a letter (A, B, C, etc.). You do not know');
            lines.push('which model produced which answer.');
            lines.push('');
            lines.push('Score each answer on the following dimensions (1-5 scale):');
            lines.push('');
            lines.push('  Accuracy      - Are the facts, standards, and procedures correct?');
            lines.push('  Completeness  - Does it cover all relevant aspects of the question?');
            lines.push('  Clarity       - Is it well-organized and easy to follow?');
            lines.push('  Faithfulness  - Does it avoid hallucinated facts or made-up references?');
            lines.push('  Overall       - Holistic quality considering all dimensions above.');
            lines.push('');
            lines.push('After scoring, select a winner (the best overall answer).');
            lines.push('Provide a brief justification for your scores and winner selection.');
            lines.push('');
            lines.push('='.repeat(80));
            lines.push('PROMPT');
            lines.push('='.repeat(80));
            lines.push('');
            lines.push(`User query: ${query.user_message}`);
            lines.push('');

            query.slots.forEach((slot, i) => {
              const label = String.fromCharCode(65 + i);
              lines.push('='.repeat(80));
              lines.push(`ANSWER ${label}`);
              lines.push('='.repeat(80));
              lines.push('');
              lines.push(slot.response);
              lines.push('');
            });

            if (localEvalScores.length > 0) {
              lines.push('='.repeat(80));
              lines.push('INTERNAL EVALUATION (for comparison — do not let this bias your scoring)');
              lines.push('='.repeat(80));
              lines.push('');
              lines.push('Dimension'.padEnd(16) + localEvalScores.map(s => `Answer ${s.answer_label}`.padEnd(12)).join(''));
              lines.push('-'.repeat(16 + localEvalScores.length * 12));
              for (const dim of ['accuracy', 'completeness', 'clarity', 'faithfulness', 'overall'] as const) {
                const dimLabel = dim.charAt(0).toUpperCase() + dim.slice(1);
                lines.push(dimLabel.padEnd(16) + localEvalScores.map(s => `${s[dim]}/5`.padEnd(12)).join(''));
              }
              lines.push('');
              if (localEvalWinner) {
                lines.push(`Internal winner: Answer ${localEvalWinner}`);
              }
              if (localEvalText) {
                lines.push('');
                lines.push('Internal verdict:');
                lines.push(localEvalText);
              }
            }

            lines.push('');
            lines.push('='.repeat(80));
            lines.push('END OF EVALUATION FILE');
            lines.push('='.repeat(80));

            const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `corvus-blind-eval-q${query.id}.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }}>
            Export Blind Evaluation (.txt)
          </button>
        </Section>
      )}

      <RefinePanel queryId={query.id} hasEval={!!localEvalText} hasNeurons={hasNeurons} initialRefineResult={query.pending_refine} onNavigateToNeuron={onNavigateToNeuron} />

      {query.refinements && query.refinements.length > 0 && (
        <Section title={`Applied Refinements (${query.refinements.length})`} defaultOpen={true}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {query.refinements.map(r => (
              <div key={r.id} style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 6,
                padding: '10px 14px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    borderRadius: 3,
                    fontWeight: 600,
                    background: r.action === 'create' ? 'rgba(34,197,94,0.15)' : 'rgba(250,204,21,0.15)',
                    color: r.action === 'create' ? '#22c55e' : '#facc15',
                  }}>
                    {r.action === 'create' ? 'CREATED' : 'UPDATED'}
                  </span>
                  <span
                    style={{ fontSize: '0.85rem', color: 'var(--text-bright, #e0e0e0)', cursor: onNavigateToNeuron ? 'pointer' : undefined }}
                    onClick={onNavigateToNeuron ? () => onNavigateToNeuron(r.neuron_id) : undefined}
                    title={onNavigateToNeuron ? 'View in Explorer' : undefined}
                  >
                    <span style={{ color: '#60a5fa', textDecoration: onNavigateToNeuron ? 'underline' : undefined }}>#{r.neuron_id}</span> {r.neuron_label ?? ''}
                  </span>
                  {r.field && <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>{r.field}</span>}
                </div>
                {r.action === 'update' && r.old_value && r.new_value && (
                  <div style={{ fontSize: '0.8rem', marginTop: 4 }}>
                    <div style={{ color: '#f87171', opacity: 0.7 }}>{r.old_value.length > 200 ? r.old_value.slice(0, 200) + '...' : r.old_value}</div>
                    <div style={{ color: '#4ade80', marginTop: 2 }}>{r.new_value.length > 200 ? r.new_value.slice(0, 200) + '...' : r.new_value}</div>
                  </div>
                )}
                {r.action === 'create' && r.new_value && (
                  <div style={{ fontSize: '0.8rem', color: '#4ade80', marginTop: 4 }}>{r.new_value}</div>
                )}
                {r.reason && <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: 4 }}>{r.reason}</div>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {hasNeurons && query.assembled_prompt && (
        <Section title="Assembled System Prompt" defaultOpen={false}>
          <div className="response-text">{query.assembled_prompt}</div>
        </Section>
      )}
    </>
  );
}
