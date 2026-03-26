/**
 * Visual Graph Experiment — D3.js SVG organic tree visualization.
 * Renders the most recent query's neuron firing as a top-down tree
 * with curved bezier edges, proportional width (Reingold-Tilford),
 * glow effects, and a layer-staggered pulse animation.
 *
 * Isolated experiment — does NOT touch ChatNeuronViz, SigmaGraph,
 * or graphology-adapter.
 */

import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { fetchQueryHistory, fetchQueryDetail, fetchSpreadTrail } from '../api';
import type { NeuronScoreResponse, SpreadTrailResponse } from '../types';
import type { QueryDetail } from '../types';
import { DEPT_COLORS } from '../constants';

// ────────── Constants ──────────

const LAYER_LABELS = ['Dept', 'Role', 'Task', 'System', 'Decision', 'Output'];
const PROMPT_COLOR = '#3b82f6';
const SPREAD_RING_COLOR = '#e8a735';
const MIN_R = 3;
const MAX_R = 13;
const NODE_X_SPACING = 26;
const LAYER_Y_SPACING = 110;
const PULSE_MS_PER_LAYER = 500;

// ────────── Helpers ──────────

function deptColor(dept: string | null): string {
  return DEPT_COLORS[dept ?? ''] ?? '#4a5568';
}

function shortDept(dept: string): string {
  return dept
    .replace('Manufacturing & Operations', 'Mfg & Ops')
    .replace('Contracts & Compliance', 'Contracts')
    .replace('Business Development', 'BD')
    .replace('Executive Leadership', 'Executive')
    .replace('Administrative & Support', 'Admin')
    .replace('Program Management', 'Program Mgmt');
}

/** Cubic bezier S-curve for parent→child edges (vertical tree) */
function bezierEdge(x1: number, y1: number, x2: number, y2: number): string {
  const my = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`;
}

/** Quadratic bezier arc for co-firing edges (perpendicular curvature) */
function arcEdge(x1: number, y1: number, x2: number, y2: number, idx: number): string {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const sign = idx % 2 === 0 ? 1 : -1;
  const curvature = dist * 0.2 * sign;
  const mx = (x1 + x2) / 2 + (-dy / dist) * curvature;
  const my = (y1 + y2) / 2 + (dx / dist) * curvature;
  return `M ${x1},${y1} Q ${mx},${my} ${x2},${y2}`;
}

// ────────── Tree data ──────────

interface TreeNodeData {
  key: string;
  neuron_id?: number;
  label: string;
  department: string;
  layer: number;
  combined: number;
  spread_boost: number;
  isPrompt?: boolean;
  isBridge?: boolean;
  summary?: string | null;
  burst?: number;
  impact?: number;
  precision?: number;
  novelty?: number;
  recency?: number;
  relevance?: number;
  children: TreeNodeData[];
}

type AncestorMap = Map<number, { id: number; label: string; department: string | null; layer: number; parent_id: number | null }>;

function buildHierarchyTree(
  scores: NeuronScoreResponse[],
  ancestorData: AncestorMap,
): TreeNodeData {
  // Root prompt node
  const root: TreeNodeData = {
    key: '__prompt__', label: 'Prompt', department: '', layer: -1,
    combined: 0, spread_boost: 0, isPrompt: true, children: [],
  };

  // Map all neurons by id
  const nodeMap = new Map<number, TreeNodeData>();
  const allIds = new Set<number>();

  // Ancestor bridge nodes
  for (const [, anc] of ancestorData) {
    allIds.add(anc.id);
    nodeMap.set(anc.id, {
      key: `n-${anc.id}`, neuron_id: anc.id, label: anc.label || `#${anc.id}`,
      department: anc.department ?? 'Unknown', layer: anc.layer,
      combined: 0, spread_boost: 0, isBridge: true, children: [],
    });
  }

  // Fired neurons (overwrite bridge entries if same id)
  for (const n of scores) {
    allIds.add(n.neuron_id);
    nodeMap.set(n.neuron_id, {
      key: `n-${n.neuron_id}`, neuron_id: n.neuron_id, label: n.label || `#${n.neuron_id}`,
      department: n.department ?? 'Unknown', layer: n.layer,
      combined: n.combined, spread_boost: n.spread_boost,
      summary: n.summary, burst: n.burst, impact: n.impact,
      precision: n.precision, novelty: n.novelty, recency: n.recency,
      relevance: n.relevance, children: [],
    });
  }

  // Build parent→child relationships
  for (const [id, node] of nodeMap) {
    // Find parent from scores or ancestors
    const scoreEntry = scores.find(s => s.neuron_id === id);
    const ancEntry = ancestorData.get(id);
    const parentId = scoreEntry?.parent_id ?? ancEntry?.parent_id ?? null;

    if (parentId != null && nodeMap.has(parentId)) {
      nodeMap.get(parentId)!.children.push(node);
    } else {
      root.children.push(node);
    }
  }

  // Sort children by department then score for spatial coherence
  const sortChildren = (node: TreeNodeData) => {
    node.children.sort((a, b) => {
      if (a.department !== b.department) return a.department.localeCompare(b.department);
      return b.combined - a.combined;
    });
    for (const child of node.children) sortChildren(child);
  };
  sortChildren(root);

  return root;
}

// ────────── Component ──────────

export default function VisualGraphExperiment() {
  const [queryDetail, setQueryDetail] = useState<QueryDetail | null>(null);
  const [trailData, setTrailData] = useState<SpreadTrailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ancestorData, setAncestorData] = useState<AncestorMap>(new Map());
  const [hoverNode, setHoverNode] = useState<TreeNodeData | null>(null);

  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const pulseIdRef = useRef(0); // for cancelling stale animations

  // ── Data fetching (unchanged from prior version) ──

  useEffect(() => {
    (async () => {
      try {
        const history = await fetchQueryHistory();
        if (history.length === 0) { setError('No queries found'); setLoading(false); return; }
        const latest = history[0];
        const detail = await fetchQueryDetail(latest.id);
        setQueryDetail(detail);
        const trail = await fetchSpreadTrail(latest.id).catch(() => null);
        setTrailData(trail);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!queryDetail) return;
    const neurons = queryDetail.neuron_hits;
    if (neurons.length === 0) return;
    const neuronIdSet = new Set(neurons.map(n => n.neuron_id));
    const missingParents = new Set<number>();
    for (const n of neurons) {
      if (n.parent_id != null && !neuronIdSet.has(n.parent_id)) {
        missingParents.add(n.parent_id);
      }
    }
    if (missingParents.size === 0) { setAncestorData(new Map()); return; }
    const fetchAncestors = async () => {
      const map: AncestorMap = new Map();
      const toFetch = [...missingParents];
      for (let depth = 0; depth < 6 && toFetch.length > 0; depth++) {
        const batch = toFetch.splice(0, toFetch.length);
        const results = await Promise.all(
          batch.map(id => fetch(`/api/neurons/${id}`).then(r => r.ok ? r.json() : null).catch(() => null))
        );
        for (const r of results) {
          if (!r) continue;
          if (!map.has(r.id)) map.set(r.id, { id: r.id, label: r.label, department: r.department, layer: r.layer, parent_id: r.parent_id });
          if (r.parent_id != null && !neuronIdSet.has(r.parent_id) && !map.has(r.parent_id)) toFetch.push(r.parent_id);
        }
      }
      setAncestorData(map);
    };
    fetchAncestors();
  }, [queryDetail]);

  const neuronScores: NeuronScoreResponse[] = useMemo(() => {
    if (!queryDetail) return [];
    return queryDetail.neuron_hits.map(h => ({ ...h }));
  }, [queryDetail]);

  // ── Tree layout ──

  const treeData = useMemo(() => {
    if (neuronScores.length === 0) return null;
    const rootData = buildHierarchyTree(neuronScores, ancestorData);
    const hierarchy = d3.hierarchy(rootData, d => d.children.length > 0 ? d.children : undefined);

    const treeLayout = d3.tree<TreeNodeData>()
      .nodeSize([NODE_X_SPACING, LAYER_Y_SPACING])
      .separation((a, b) => a.data.department !== b.data.department ? 2.2 : 1);

    const laidOut = treeLayout(hierarchy);
    const nodes = laidOut.descendants();
    const links = laidOut.links();

    // Bounds
    let minX = Infinity, maxX = -Infinity, maxY = 0;
    for (const n of nodes) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y > maxY) maxY = n.y;
    }

    // Build position lookup for co-firing edges
    const posMap = new Map<number, { x: number; y: number }>();
    for (const n of nodes) {
      if (n.data.neuron_id != null) posMap.set(n.data.neuron_id, { x: n.x, y: n.y });
    }

    return { nodes, links, posMap, bounds: { minX, maxX, maxY } };
  }, [neuronScores, ancestorData]);

  // ── Max score for sizing ──
  const maxScore = useMemo(() => Math.max(...neuronScores.map(s => s.combined), 0.001), [neuronScores]);

  // ── Render D3 SVG ──

  const renderTree = useCallback(() => {
    if (!svgRef.current || !treeData || !containerRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { nodes, links, posMap, bounds } = treeData;
    const treeWidth = bounds.maxX - bounds.minX + 200;
    const treeHeight = bounds.maxY + 100;

    // Defs: glow filters
    const defs = svg.append('defs');

    const edgeGlow = defs.append('filter').attr('id', 'edge-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
    edgeGlow.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '2').attr('result', 'blur');
    const edgeMerge = edgeGlow.append('feMerge');
    edgeMerge.append('feMergeNode').attr('in', 'blur');
    edgeMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const nodeGlow = defs.append('filter').attr('id', 'node-glow').attr('x', '-100%').attr('y', '-100%').attr('width', '300%').attr('height', '300%');
    nodeGlow.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '3').attr('result', 'blur');
    const nodeMerge = nodeGlow.append('feMerge');
    nodeMerge.append('feMergeNode').attr('in', 'blur');
    nodeMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Main group (zoom target)
    const g = svg.append('g').attr('class', 'tree-main');

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.08, 5])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);
    zoomRef.current = zoom;

    // Initial zoom-to-fit
    const rect = containerRef.current.getBoundingClientRect();
    const scaleX = rect.width / (treeWidth + 80);
    const scaleY = rect.height / (treeHeight + 80);
    const initScale = Math.min(scaleX, scaleY, 1);
    const centerX = (bounds.minX + bounds.maxX) / 2;
    const tx = rect.width / 2 - centerX * initScale;
    const ty = 40 * initScale;
    svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(initScale));

    // ── Edge glow layer ──
    const glowGroup = g.append('g').attr('class', 'edge-glow-layer');
    for (const link of links) {
      const color = deptColor(link.target.data.department);
      glowGroup.append('path')
        .attr('d', bezierEdge(link.source.x, link.source.y, link.target.x, link.target.y))
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 4)
        .attr('stroke-opacity', 0.08)
        .attr('filter', 'url(#edge-glow)');
    }

    // ── Edge core layer ──
    const coreGroup = g.append('g').attr('class', 'edge-core-layer');
    for (const link of links) {
      const target = link.target.data;
      const color = deptColor(target.department);
      const scoreT = maxScore > 0 ? target.combined / maxScore : 0;
      const sw = 0.8 + scoreT * 1.5;
      const opacity = target.isBridge ? 0.15 : 0.25 + scoreT * 0.4;
      coreGroup.append('path')
        .attr('class', 'hierarchy-edge')
        .attr('d', bezierEdge(link.source.x, link.source.y, link.target.x, link.target.y))
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', sw)
        .attr('stroke-opacity', opacity)
        .attr('data-depth', link.target.depth);
    }

    // ── Co-firing edges ──
    if (trailData?.edges) {
      const cfGroup = g.append('g').attr('class', 'cofiring-layer');
      let idx = 0;
      for (const e of trailData.edges) {
        const src = posMap.get(e.source_id);
        const tgt = posMap.get(e.target_id);
        if (!src || !tgt) continue;
        cfGroup.append('path')
          .attr('d', arcEdge(src.x, src.y, tgt.x, tgt.y, idx++))
          .attr('fill', 'none')
          .attr('stroke', '#94a3b8')
          .attr('stroke-width', 0.4 + e.weight * 0.8)
          .attr('stroke-opacity', 0.12)
          .attr('stroke-dasharray', '3 4');
      }
    }

    // ── Node layer ──
    const nodeGroup = g.append('g').attr('class', 'node-layer');
    for (const n of nodes) {
      const d = n.data;
      const isPrompt = !!d.isPrompt;
      const scoreT = maxScore > 0 ? d.combined / maxScore : 0;
      const r = isPrompt ? 14 : MIN_R + scoreT * (MAX_R - MIN_R);
      const color = isPrompt ? PROMPT_COLOR : deptColor(d.department);
      const opacity = d.isBridge ? 0.35 : 0.6 + scoreT * 0.4;

      const ng = nodeGroup.append('g')
        .attr('transform', `translate(${n.x},${n.y})`)
        .style('cursor', 'pointer')
        .on('mouseenter', () => setHoverNode(d))
        .on('mouseleave', () => setHoverNode(null));

      // Glow halo
      ng.append('circle')
        .attr('r', r + 4)
        .attr('fill', color)
        .attr('fill-opacity', 0.08)
        .attr('filter', 'url(#node-glow)');

      // Spread boost ring
      if (d.spread_boost > 0) {
        ng.append('circle')
          .attr('r', r + 2)
          .attr('fill', 'none')
          .attr('stroke', SPREAD_RING_COLOR)
          .attr('stroke-width', 1.5)
          .attr('stroke-opacity', 0.7);
      }

      // Main circle
      ng.append('circle')
        .attr('r', r)
        .attr('fill', color)
        .attr('fill-opacity', opacity)
        .attr('stroke', isPrompt ? '#fff' : color)
        .attr('stroke-width', isPrompt ? 2 : 0.5)
        .attr('stroke-opacity', 0.5);

      // Label (skip bridge nodes and tiny scores)
      if (!d.isBridge && (isPrompt || scoreT > 0.15)) {
        const labelText = d.label.length > 16 ? d.label.slice(0, 15) + '…' : d.label;
        ng.append('text')
          .attr('y', r + 11)
          .attr('text-anchor', 'middle')
          .attr('font-size', isPrompt ? '10px' : '8px')
          .attr('font-weight', isPrompt ? '700' : '500')
          .attr('fill', 'var(--text, #e2e8f0)')
          .attr('fill-opacity', 0.8)
          .text(labelText);
      }
    }
  }, [treeData, trailData, maxScore]);

  // ── Pulse animation ──

  const runPulse = useCallback(() => {
    if (!svgRef.current || !treeData) return;
    const id = ++pulseIdRef.current;
    const svg = d3.select(svgRef.current);
    const edges = svg.selectAll<SVGPathElement, unknown>('.hierarchy-edge');

    // Compute total length and set initial dash state
    edges.each(function () {
      const path = this as SVGPathElement;
      const len = path.getTotalLength();
      d3.select(path)
        .attr('stroke-dasharray', `${len}`)
        .attr('stroke-dashoffset', `${len}`);
    });

    // Animate by depth
    const maxDepth = d3.max(treeData.nodes, n => n.depth) ?? 6;
    for (let depth = 0; depth <= maxDepth; depth++) {
      edges
        .filter(function () { return Number(d3.select(this).attr('data-depth')) === depth; })
        .transition()
        .delay(depth * PULSE_MS_PER_LAYER)
        .duration(PULSE_MS_PER_LAYER)
        .ease(d3.easeQuadOut)
        .attr('stroke-dashoffset', '0')
        .on('end', function () {
          // Only clear dasharray if this pulse is still current
          if (pulseIdRef.current === id) {
            d3.select(this).attr('stroke-dasharray', null);
          }
        });
    }
  }, [treeData]);

  // Render + pulse when data is ready
  useEffect(() => {
    renderTree();
    // Small delay to let the SVG paint before animating
    const timer = setTimeout(() => runPulse(), 100);
    return () => {
      clearTimeout(timer);
      if (svgRef.current) {
        d3.select(svgRef.current).selectAll('.hierarchy-edge').interrupt();
      }
    };
  }, [renderTree, runPulse]);

  // ── Zoom controls ──

  const zoomIn = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(zoomRef.current.scaleBy, 1.4);
  }, []);
  const zoomOut = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(zoomRef.current.scaleBy, 0.7);
  }, []);
  const zoomFit = useCallback(() => {
    if (!svgRef.current || !zoomRef.current || !containerRef.current || !treeData) return;
    const rect = containerRef.current.getBoundingClientRect();
    const { bounds } = treeData;
    const tw = bounds.maxX - bounds.minX + 200;
    const th = bounds.maxY + 100;
    const s = Math.min(rect.width / (tw + 80), rect.height / (th + 80), 1);
    const cx = (bounds.minX + bounds.maxX) / 2;
    d3.select(svgRef.current).transition().duration(500).call(
      zoomRef.current.transform,
      d3.zoomIdentity.translate(rect.width / 2 - cx * s, 40 * s).scale(s),
    );
  }, [treeData]);

  // ── Early returns ──

  if (loading) return <div style={{ padding: 24, color: 'var(--text-dim)' }}>Loading last query...</div>;
  if (error) return <div style={{ padding: 24 }} className="error-msg">{error}</div>;
  if (!queryDetail) return null;

  const neurons = queryDetail.neuron_hits;
  const deptCounts = new Map<string, number>();
  for (const n of neurons) {
    const d = n.department || 'Unknown';
    deptCounts.set(d, (deptCounts.get(d) || 0) + 1);
  }
  const spreadCount = neurons.filter(n => n.spread_boost > 0).length;

  // ── JSX ──

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>Visual Graph Experiment</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          Query #{queryDetail.id}: {queryDetail.user_message.slice(0, 60)}...
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, fontSize: '0.72rem', color: 'var(--text-dim)' }}>
        <span>{neurons.length} neurons</span>
        <span>&middot;</span>
        <span>{trailData?.edges?.length ?? 0} co-firing edges</span>
        <span>&middot;</span>
        <span>{spreadCount} spread-boosted</span>
        <span>&middot;</span>
        <span style={{ color: 'var(--accent)' }}>D3 organic tree — Reingold-Tilford layout</span>
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0, gap: 12 }}>
        {/* SVG container */}
        <div ref={containerRef} style={{ flex: 1, minWidth: 0, position: 'relative', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)', background: 'var(--bg)' }}>
          <svg ref={svgRef} width="100%" height="100%" />

          {/* Zoom controls */}
          <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[
              { label: '+', fn: zoomIn, title: 'Zoom in' },
              { label: '\u2212', fn: zoomOut, title: 'Zoom out' },
              { label: '\u2b1c', fn: zoomFit, title: 'Fit' },
              { label: '\u21bb', fn: runPulse, title: 'Replay pulse' },
            ].map(b => (
              <button key={b.label} onClick={b.fn} title={b.title} style={{
                width: 28, height: 28, borderRadius: 4, border: '1px solid var(--border)',
                background: 'var(--bg-card)', color: 'var(--text)', cursor: 'pointer',
                fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>{b.label}</button>
            ))}
          </div>

          {/* Hover popup */}
          {hoverNode && !hoverNode.isPrompt && (
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              background: 'rgba(15, 23, 42, 0.92)', backdropFilter: 'blur(8px)',
              borderTop: '1px solid rgba(59, 130, 246, 0.2)',
              padding: '10px 16px', fontSize: '0.78rem', color: '#e2e8f0',
              zIndex: 20, pointerEvents: 'none',
              display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap',
            }}>
              <div style={{ minWidth: 160 }}>
                <div style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: 2 }}>{hoverNode.label}</div>
                <div style={{ color: deptColor(hoverNode.department), fontSize: '0.72rem' }}>
                  {shortDept(hoverNode.department)} &middot; {LAYER_LABELS[hoverNode.layer] ?? `L${hoverNode.layer}`}
                </div>
                {hoverNode.summary && (
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem', marginTop: 4, maxWidth: 300 }}>{hoverNode.summary}</div>
                )}
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <div><span style={{ color: '#64748b' }}>Combined</span> <strong>{hoverNode.combined.toFixed(3)}</strong></div>
                {hoverNode.burst != null && <div><span style={{ color: '#64748b' }}>Burst</span> {hoverNode.burst.toFixed(3)}</div>}
                {hoverNode.impact != null && <div><span style={{ color: '#64748b' }}>Impact</span> {hoverNode.impact.toFixed(3)}</div>}
                {hoverNode.precision != null && <div><span style={{ color: '#64748b' }}>Precision</span> {hoverNode.precision.toFixed(3)}</div>}
                {hoverNode.novelty != null && <div><span style={{ color: '#64748b' }}>Novelty</span> {hoverNode.novelty.toFixed(3)}</div>}
                {hoverNode.recency != null && <div><span style={{ color: '#64748b' }}>Recency</span> {hoverNode.recency.toFixed(3)}</div>}
                {hoverNode.relevance != null && <div><span style={{ color: '#64748b' }}>Relevance</span> {hoverNode.relevance.toFixed(3)}</div>}
              </div>
              {hoverNode.spread_boost > 0 && (
                <div style={{ color: SPREAD_RING_COLOR }}>Spread +{hoverNode.spread_boost.toFixed(3)}</div>
              )}
            </div>
          )}
        </div>

        {/* Legend sidebar */}
        <div style={{ width: 170, flexShrink: 0, fontSize: '0.7rem' }}>
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Departments</div>
            {Array.from(deptCounts.entries()).sort((a, b) => b[1] - a[1]).map(([dept, count]) => (
              <div key={dept} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: DEPT_COLORS[dept] || '#4a5568', flexShrink: 0 }} />
                <span style={{ color: 'var(--text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{shortDept(dept)}</span>
                <span style={{ color: 'var(--text-dim)' }}>{count}</span>
              </div>
            ))}
          </div>
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Layers</div>
            {LAYER_LABELS.map((lbl, layer) => {
              const count = neurons.filter(n => n.layer === layer).length;
              const pct = neurons.length > 0 ? (count / neurons.length) * 100 : 0;
              return (
                <div key={layer} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: '0.58rem', color: 'var(--text-dim)', width: 46 }}>L{layer} {lbl}</span>
                  <div style={{ flex: 1, height: 3, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', borderRadius: 2, background: 'var(--accent)', width: `${pct}%` }} />
                  </div>
                  <span style={{ fontSize: '0.58rem', color: count > 0 ? 'var(--text)' : 'var(--text-dim)', width: 14, textAlign: 'right' }}>{count}</span>
                </div>
              );
            })}
          </div>
          <div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Strongest</div>
            {neuronScores.slice(0, 5).map((n, i) => (
              <div key={n.neuron_id} style={{
                padding: '3px 6px', marginBottom: 2, borderRadius: 4,
                background: i === 0 ? 'rgba(59,130,246,0.08)' : 'transparent',
                border: i === 0 ? '1px solid rgba(59,130,246,0.15)' : '1px solid transparent',
              }}>
                <div style={{ fontSize: '0.68rem', fontWeight: i === 0 ? 600 : 400, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {n.label || `#${n.neuron_id}`}
                </div>
                <div style={{ fontSize: '0.58rem', color: '#64748b', display: 'flex', gap: 6 }}>
                  <span>{n.combined.toFixed(3)}</span>
                  <span style={{ color: deptColor(n.department) }}>{shortDept(n.department || '')}</span>
                  {n.spread_boost > 0 && <span style={{ color: SPREAD_RING_COLOR }}>+{n.spread_boost.toFixed(3)}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
