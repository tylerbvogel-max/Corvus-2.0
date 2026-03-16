import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { fetchSpreadTrail } from '../api';
import type { NeuronScoreResponse, SpreadTrailResponse } from '../types';
import { DEPT_COLORS } from '../constants';

/**
 * 2D force-directed graph visualization for neuron firing.
 * Hierarchical parent→child edges create a real tree topology.
 * Prompt node pinned at top; hover shows full details in a bottom popup.
 */

const LAYER_LABELS = ['Dept', 'Role', 'Task', 'System', 'Decision', 'Output'];
const CONCEPT_COLOR = '#e879f9';

interface Props {
  neuronScores: NeuronScoreResponse[];
  neuronsActivated: number;
  queryId?: number;
  onNavigateToNeuron?: (id: number) => void;
  collapsed?: boolean;
  fullSize?: boolean;
}

interface GNode {
  id: string;
  neuron_id?: number;
  label: string;
  department: string;
  layer: number;
  combined: number;
  spread_boost: number;
  isPrompt?: boolean;
  isConcept?: boolean;
  parent_id?: number | null;
  summary?: string | null;
  burst?: number;
  impact?: number;
  precision?: number;
  novelty?: number;
  recency?: number;
  relevance?: number;
  val: number; // controls node size
  color: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

interface GLink {
  source: string;
  target: string;
  weight: number;
  isPromptLink?: boolean;
  isHierarchy?: boolean;
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

export default function ChatNeuronViz({ neuronScores, neuronsActivated, queryId, onNavigateToNeuron, collapsed, fullSize }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);
  const [trailData, setTrailData] = useState<SpreadTrailResponse | null>(null);
  const [hoverNode, setHoverNode] = useState<GNode | null>(null);

  const neurons = neuronScores;
  const isExpanded = !collapsed;
  // Use measured container height when available, fall back to sensible defaults
  const vizHeight = dimensions?.height || (fullSize ? 480 : 600);

  // Measure container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (w > 0 && h > 0) setDimensions(prev => (prev?.width === w && prev?.height === h) ? prev : { width: w, height: h });
    };
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    requestAnimationFrame(measure);
    return () => ro.disconnect();
  }, []);

  // Fetch spread trail for edges
  useEffect(() => {
    if (queryId) {
      fetchSpreadTrail(queryId).then(setTrailData).catch(() => setTrailData(null));
    }
  }, [queryId]);

  // Fetch ancestor neurons for hierarchy bridge nodes
  const [ancestorData, setAncestorData] = useState<Map<number, { id: number; label: string; department: string | null; layer: number; parent_id: number | null }>>(new Map());

  useEffect(() => {
    if (neurons.length === 0) return;
    // Collect all parent_ids that aren't in the neuron set
    const neuronIdSet = new Set(neurons.map(n => n.neuron_id));
    const missingParents = new Set<number>();
    for (const n of neurons) {
      if (n.parent_id != null && !neuronIdSet.has(n.parent_id)) {
        missingParents.add(n.parent_id);
      }
    }
    if (missingParents.size === 0) { setAncestorData(new Map()); return; }

    // Fetch missing ancestors from the API
    const fetchAncestors = async () => {
      const map = new Map<number, { id: number; label: string; department: string | null; layer: number; parent_id: number | null }>();
      const toFetch = [...missingParents];
      // Iteratively fetch ancestors up the chain (max 6 layers)
      for (let depth = 0; depth < 6 && toFetch.length > 0; depth++) {
        const batch = toFetch.splice(0, toFetch.length);
        const results = await Promise.all(
          batch.map(id =>
            fetch(`/api/neurons/${id}`).then(r => r.ok ? r.json() : null).catch(() => null)
          )
        );
        for (const r of results) {
          if (!r) continue;
          if (!map.has(r.id)) {
            map.set(r.id, { id: r.id, label: r.label, department: r.department, layer: r.layer, parent_id: r.parent_id });
          }
          // If this ancestor's parent is also missing, queue it
          if (r.parent_id != null && !neuronIdSet.has(r.parent_id) && !map.has(r.parent_id)) {
            toFetch.push(r.parent_id);
          }
        }
      }
      setAncestorData(map);
    };
    fetchAncestors();
  }, [neurons]);

  // Build graph data with hierarchical parent→child edges
  const graphData = useMemo(() => {
    if (neurons.length === 0) return { nodes: [] as GNode[], links: [] as GLink[] };

    const maxScore = Math.max(...neurons.map(n => n.combined), 0.001);

    const nodes: GNode[] = [];
    const links: GLink[] = [];
    const nodeIds = new Set<string>();

    // Prompt node at center-top
    const promptNode: GNode = {
      id: '__prompt__',
      label: 'Prompt',
      department: '',
      layer: -1,
      combined: 0,
      spread_boost: 0,
      isPrompt: true,
      val: 5,
      color: '#3b82f6',
    };
    nodes.push(promptNode);
    nodeIds.add('__prompt__');

    // Add ancestor bridge nodes first (smaller, dimmed)
    for (const [, anc] of ancestorData) {
      const id = `n-${anc.id}`;
      if (nodeIds.has(id)) continue;
      const dept = anc.department || 'Unknown';
      const isConcept = anc.layer === -1;
      nodes.push({
        id,
        neuron_id: anc.id,
        label: anc.label || `#${anc.id}`,
        department: dept,
        layer: anc.layer,
        combined: 0,
        spread_boost: 0,
        isConcept,
        parent_id: anc.parent_id,
        val: 1, // small bridge node
        color: isConcept ? CONCEPT_COLOR + '88' : ((DEPT_COLORS[dept] || '#4a5568') + '88'),
      });
      nodeIds.add(id);
    }

    // Sort neurons by layer so parents are added before children
    const sortedNeurons = [...neurons].sort((a, b) => a.layer - b.layer);

    // Neuron nodes
    for (const n of sortedNeurons) {
      const dept = n.department || 'Unknown';
      const isConcept = n.layer === -1;
      const id = `n-${n.neuron_id}`;
      nodes.push({
        id,
        neuron_id: n.neuron_id,
        label: n.label || `#${n.neuron_id}`,
        department: dept,
        layer: n.layer,
        combined: n.combined,
        spread_boost: n.spread_boost,
        isConcept,
        parent_id: n.parent_id,
        summary: n.summary,
        burst: n.burst,
        impact: n.impact,
        precision: n.precision,
        novelty: n.novelty,
        recency: n.recency,
        relevance: n.relevance,
        val: 1 + (n.combined / maxScore) * 3,
        color: isConcept ? CONCEPT_COLOR : (DEPT_COLORS[dept] || '#4a5568'),
      });
      nodeIds.add(id);
    }

    // Include trail nodes that aren't already in our neuron list (concept neurons, etc.)
    const trailNodes = trailData?.nodes ?? [];
    for (const tn of trailNodes) {
      const id = `n-${tn.id}`;
      if (nodeIds.has(id)) continue;
      const dept = tn.department || 'Concepts';
      const isConcept = tn.layer === -1;
      nodes.push({
        id,
        neuron_id: tn.id,
        label: tn.label || `#${tn.id}`,
        department: dept,
        layer: tn.layer,
        combined: tn.combined,
        spread_boost: tn.spread_boost,
        isConcept,
        val: 1 + (tn.combined / maxScore) * 2,
        color: isConcept ? CONCEPT_COLOR : (DEPT_COLORS[dept] || '#4a5568'),
      });
      nodeIds.add(id);
    }

    // Build hierarchy edges: parent→child if parent is in graph, else prompt→child
    for (const node of nodes) {
      if (node.isPrompt) continue;
      const parentKey = node.parent_id != null ? `n-${node.parent_id}` : null;
      if (parentKey && nodeIds.has(parentKey)) {
        links.push({
          source: parentKey,
          target: node.id,
          weight: Math.max(node.combined / maxScore, 0.2),
          isHierarchy: true,
        });
      } else {
        links.push({
          source: '__prompt__',
          target: node.id,
          weight: Math.max(node.combined / maxScore, 0.2),
          isPromptLink: true,
        });
      }
    }

    // Spread trail edges (co-firing cross-connections)
    const edges = trailData?.edges ?? [];
    for (const e of edges) {
      const srcId = `n-${e.source_id}`;
      const tgtId = `n-${e.target_id}`;
      if (nodeIds.has(srcId) && nodeIds.has(tgtId)) {
        links.push({
          source: srcId,
          target: tgtId,
          weight: e.weight,
        });
      }
    }

    return { nodes, links };
  }, [neurons, trailData, ancestorData]);

  // Configure forces: pin prompt at top, pull neurons downward by layer
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || graphData.nodes.length === 0) return;

    // Pin prompt node at top
    const promptNode = graphData.nodes.find(n => n.isPrompt);
    const promptY = 0;
    if (promptNode) {
      promptNode.fx = 0;
      promptNode.fy = promptY;
    }

    // Strong layer-based Y positioning with hard ceiling clamp
    const layerSpacing = 80;
    const ceilingY = promptY + 20; // no node goes above this
    fg.d3Force('y', null);
    fg.d3Force('gravity', (alpha: number) => {
      for (const node of graphData.nodes) {
        if (node.isPrompt) continue;
        const layerDepth = node.layer >= 0 ? node.layer : 3;
        const targetY = promptY + (layerDepth + 1) * layerSpacing;
        node.vy = ((node.vy || 0) + (targetY - (node.y || 0)) * 0.1 * alpha);
        // Hard ceiling: push down any node that drifts above prompt
        if ((node.y || 0) < ceilingY) {
          node.y = ceilingY;
          node.vy = Math.abs(node.vy || 0);
        }
      }
    });

    // Weaker charge so nodes don't blow apart vertically
    fg.d3Force('x', null);
    fg.d3Force('charge')?.strength(-60);

    fg.d3ReheatSimulation();

    // Zoom to fit, then shift view so prompt is near top of screen
    const timer = setTimeout(() => {
      fg.zoomToFit(400, 50);
      setTimeout(() => {
        // Find vertical extent of all nodes
        const ys = graphData.nodes.map(n => n.y || 0);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        const span = maxY - minY;
        // Center on a point shifted down from prompt, so prompt appears near top
        fg.centerAt(0, minY + span * 0.55, 400);
      }, 500);
    }, 1000);
    return () => clearTimeout(timer);
  }, [graphData]);

  // Custom node rendering — only show label for Prompt node
  const paintNode = useCallback((node: GNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const r = Math.sqrt(node.val || 1) * 3;

    // Glow
    ctx.beginPath();
    ctx.arc(node.x || 0, node.y || 0, r + 2, 0, 2 * Math.PI);
    ctx.fillStyle = node.color + '20';
    ctx.fill();

    // Main circle
    ctx.beginPath();
    ctx.arc(node.x || 0, node.y || 0, r, 0, 2 * Math.PI);
    if (node.isPrompt) {
      ctx.fillStyle = '#3b82f6';
      ctx.strokeStyle = '#3b82f644';
      ctx.lineWidth = 3 / globalScale;
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillStyle = node.color;
      ctx.fill();
      // Spread boost ring
      if (node.spread_boost > 0) {
        ctx.beginPath();
        ctx.arc(node.x || 0, node.y || 0, r + 2.5, 0, 2 * Math.PI);
        ctx.strokeStyle = '#e8a735';
        ctx.lineWidth = 1.5 / globalScale;
        ctx.stroke();
      }
    }

    // Only draw label for Prompt node
    if (node.isPrompt) {
      const fontSize = Math.max(10 / globalScale, 1.2);
      ctx.font = `bold ${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const label = 'Prompt';
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(
        (node.x || 0) - textWidth / 2 - 2,
        (node.y || 0) + r + 2,
        textWidth + 4,
        fontSize + 2
      );
      ctx.fillStyle = '#93c5fd';
      ctx.fillText(label, node.x || 0, (node.y || 0) + r + 3);
    }
  }, []);

  // Hit area for pointer events
  const paintPointerArea = useCallback((node: GNode, color: string, ctx: CanvasRenderingContext2D) => {
    const r = Math.sqrt(node.val || 1) * 3 + 4;
    ctx.beginPath();
    ctx.arc(node.x || 0, node.y || 0, r, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  if (neurons.length === 0) return null;

  const deptCounts = new Map<string, number>();
  for (const n of neurons) {
    const d = n.department || 'Unknown';
    deptCounts.set(d, (deptCounts.get(d) || 0) + 1);
  }
  const spreadCount = neurons.filter(n => n.spread_boost > 0).length;
  const edgeCount = trailData?.edges?.length ?? 0;

  return (
    <div className="chat-neuron-viz" style={{
      ...(fullSize ? { marginBottom: 16 } : {}),
      width: '100%',
      height: '100%',
    }}>
      {fullSize ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text)' }}>Neuron Firing</span>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
            {neuronsActivated} activated &middot; {edgeCount} edges &middot; {spreadCount} spread-boosted
          </span>
        </div>
      ) : null}
      {isExpanded && (
        <div className="chat-neuron-viz-canvas-wrap" style={{ height: '100%' }}>
          <div ref={containerRef} style={{ flex: 1, minWidth: 0, position: 'relative', height: '100%', width: '100%' }}>
            {dimensions && (
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                width={dimensions.width}
                height={vizHeight}
                backgroundColor="rgba(0,0,0,0)"
                nodeCanvasObject={paintNode}
                nodeCanvasObjectMode={() => 'replace'}
                nodePointerAreaPaint={paintPointerArea}
                nodeVal="val"
                linkColor={(link: GLink) => (link.isPromptLink || link.isHierarchy) ? '#3b82f633' : '#e8a73566'}
                linkWidth={(link: GLink) => (link.isPromptLink || link.isHierarchy) ? 0.5 : 0.8 + link.weight * 1.5}
                linkCurvature={(link: GLink) => (link.isPromptLink || link.isHierarchy) ? 0 : 0.2}
                linkDirectionalParticles={(link: GLink) => (link.isPromptLink || link.isHierarchy) ? 0 : (link.weight > 0.3 ? 2 : 0)}
                linkDirectionalParticleWidth={2}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleColor={() => '#e8a735'}
                enableNodeDrag={true}
                enableZoomInteraction={true}
                enablePanInteraction={true}
                d3AlphaDecay={0.03}
                d3VelocityDecay={0.3}
                cooldownTime={3000}
                onNodeClick={(node: GNode) => {
                  if (node.neuron_id && onNavigateToNeuron) onNavigateToNeuron(node.neuron_id);
                }}
                onNodeHover={(node: GNode | null) => setHoverNode(node)}
              />
            )}
            {/* Bottom hover detail panel */}
            {hoverNode && !hoverNode.isPrompt && (
              <div style={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                background: 'rgba(15, 23, 42, 0.92)',
                backdropFilter: 'blur(8px)',
                borderTop: '1px solid rgba(59, 130, 246, 0.2)',
                padding: '10px 16px',
                fontSize: '0.78rem',
                color: '#e2e8f0',
                zIndex: 20,
                pointerEvents: 'none',
                display: 'flex',
                gap: 24,
                alignItems: 'flex-start',
                flexWrap: 'wrap',
              }}>
                {/* Left: name + department + layer */}
                <div style={{ minWidth: 160 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: 2 }}>
                    {hoverNode.label}
                  </div>
                  <div style={{ color: hoverNode.color, fontSize: '0.72rem' }}>
                    {hoverNode.isConcept ? 'Concept' : shortDept(hoverNode.department)} · {hoverNode.isConcept ? 'Concept' : (LAYER_LABELS[hoverNode.layer] ?? `L${hoverNode.layer}`)}
                  </div>
                  {hoverNode.summary && (
                    <div style={{ color: '#94a3b8', fontSize: '0.7rem', marginTop: 4, maxWidth: 300 }}>
                      {hoverNode.summary}
                    </div>
                  )}
                </div>
                {/* Center: signal scores */}
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <div><span style={{ color: '#64748b' }}>Combined</span> <strong>{hoverNode.combined.toFixed(3)}</strong></div>
                  {hoverNode.burst != null && <div><span style={{ color: '#64748b' }}>Burst</span> {hoverNode.burst.toFixed(3)}</div>}
                  {hoverNode.impact != null && <div><span style={{ color: '#64748b' }}>Impact</span> {hoverNode.impact.toFixed(3)}</div>}
                  {hoverNode.precision != null && <div><span style={{ color: '#64748b' }}>Precision</span> {hoverNode.precision.toFixed(3)}</div>}
                  {hoverNode.novelty != null && <div><span style={{ color: '#64748b' }}>Novelty</span> {hoverNode.novelty.toFixed(3)}</div>}
                  {hoverNode.recency != null && <div><span style={{ color: '#64748b' }}>Recency</span> {hoverNode.recency.toFixed(3)}</div>}
                  {hoverNode.relevance != null && <div><span style={{ color: '#64748b' }}>Relevance</span> {hoverNode.relevance.toFixed(3)}</div>}
                </div>
                {/* Right: spread boost */}
                {hoverNode.spread_boost > 0 && (
                  <div style={{ color: '#e8a735' }}>
                    Spread +{hoverNode.spread_boost.toFixed(3)}
                  </div>
                )}
              </div>
            )}
          </div>
          {fullSize && (
            <div className="chat-neuron-viz-legend" style={{ width: 175 }}>
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Departments</div>
                {Array.from(deptCounts.entries()).sort((a, b) => b[1] - a[1]).map(([dept, count]) => (
                  <div key={dept} className="chat-neuron-viz-legend-row">
                    <span className="chat-neuron-viz-dept-dot" style={{ background: DEPT_COLORS[dept] || '#4a5568' }} />
                    <span className="chat-neuron-viz-legend-label">{shortDept(dept)}</span>
                    <span className="chat-neuron-viz-legend-count">{count}</span>
                  </div>
                ))}
                {spreadCount > 0 && (
                  <div className="chat-neuron-viz-legend-row">
                    <span className="chat-neuron-viz-dept-dot" style={{ border: '1.5px solid #e8a735', background: 'transparent' }} />
                    <span className="chat-neuron-viz-legend-label" style={{ color: '#e8a735' }}>Spread</span>
                    <span className="chat-neuron-viz-legend-count">{spreadCount}</span>
                  </div>
                )}
              </div>
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Layers</div>
                {LAYER_LABELS.map((lbl, layer) => {
                  const count = neurons.filter(s => s.layer === layer).length;
                  const pct = neurons.length > 0 ? (count / neurons.length) * 100 : 0;
                  return (
                    <div key={layer} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: '0.58rem', color: '#64748b', width: 46 }}>L{layer} {lbl}</span>
                      <div style={{ flex: 1, height: 3, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', borderRadius: 2, background: '#3b82f6', width: `${pct}%`, transition: 'width 0.5s ease' }} />
                      </div>
                      <span style={{ fontSize: '0.58rem', color: count > 0 ? 'var(--text)' : '#334155', width: 14, textAlign: 'right' }}>{count}</span>
                    </div>
                  );
                })}
              </div>
              <div>
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Strongest</div>
                {neurons.slice(0, 5).map((n, i) => (
                  <div key={n.neuron_id} style={{
                    padding: '3px 6px', marginBottom: 2, borderRadius: 4,
                    background: i === 0 ? 'rgba(59,130,246,0.08)' : 'transparent',
                    border: i === 0 ? '1px solid rgba(59,130,246,0.15)' : '1px solid transparent',
                    cursor: onNavigateToNeuron ? 'pointer' : 'default',
                  }} onClick={() => onNavigateToNeuron?.(n.neuron_id)}>
                    <div style={{ fontSize: '0.68rem', fontWeight: i === 0 ? 600 : 400, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {n.label || `#${n.neuron_id}`}
                    </div>
                    <div style={{ fontSize: '0.58rem', color: '#64748b', display: 'flex', gap: 6 }}>
                      <span>{n.combined.toFixed(3)}</span>
                      <span style={{ color: DEPT_COLORS[n.department || ''] || '#64748b' }}>{shortDept(n.department || '')}</span>
                      {n.spread_boost > 0 && <span style={{ color: '#e8a735' }}>+{n.spread_boost.toFixed(3)}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
