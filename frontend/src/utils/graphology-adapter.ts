/**
 * Adapter utilities for converting Corvus data into Graphology graphs.
 * Handles node/edge attribute mapping for both inline (ChatNeuronViz/SpreadTrail)
 * and standalone (SigmaGraphPage) visualizations.
 */

import Graph from 'graphology';
import type { NeuronScoreResponse, SpreadTrailResponse } from '../types';
import { DEPT_COLORS } from '../constants';

const CONCEPT_COLOR = '#e879f9';
const PROMPT_COLOR = '#3b82f6';
const SPREAD_RING_COLOR = '#e8a735';

/** Layer-based node sizing: higher layers = smaller */
function layerSize(layer: number): number {
  if (layer === -1) return 6; // concepts
  return Math.max(3, 10 - layer * 1.2);
}

/** Department color with optional alpha */
function deptColor(dept: string | null, alpha?: number): string {
  const color = DEPT_COLORS[dept ?? ''] ?? '#4a5568';
  if (alpha !== undefined) {
    const hex = Math.round(alpha * 255).toString(16).padStart(2, '0');
    return color + hex;
  }
  return color;
}

/**
 * Convert neuron scores + spread trail into a Graphology graph.
 * Used by ChatNeuronViz and SpreadTrail components.
 */
export function neuronScoresToGraph(
  scores: NeuronScoreResponse[],
  spreadTrail?: SpreadTrailResponse,
  ancestorData?: Map<number, { id: number; label: string; department: string | null; layer: number; parent_id: number | null }>,
): Graph {
  const graph = new Graph({ type: 'undirected', multi: true });
  if (scores.length === 0) return graph;

  const maxScore = Math.max(...scores.map(s => s.combined), 0.001);
  const nodeIds = new Set<string>();

  // Prompt node
  graph.addNode('__prompt__', {
    label: 'Prompt',
    x: 0,
    y: 0,
    size: 12,
    color: PROMPT_COLOR,
    isPrompt: true,
    department: '',
    layer: -1,
    combined: 0,
    spread_boost: 0,
  });
  nodeIds.add('__prompt__');

  // Ancestor bridge nodes (dimmed)
  if (ancestorData) {
    for (const [, anc] of ancestorData) {
      const id = `n-${anc.id}`;
      if (nodeIds.has(id)) continue;
      const isConcept = anc.layer === -1;
      graph.addNode(id, {
        label: anc.label || `#${anc.id}`,
        x: Math.random() * 200 - 100,
        y: (anc.layer + 1) * 80,
        size: layerSize(anc.layer) * 0.6,
        color: isConcept ? CONCEPT_COLOR + '88' : deptColor(anc.department, 0.53),
        department: anc.department ?? 'Unknown',
        layer: anc.layer,
        neuron_id: anc.id,
        combined: 0,
        spread_boost: 0,
        isBridge: true,
      });
      nodeIds.add(id);
    }
  }

  // Neuron nodes
  const sorted = [...scores].sort((a, b) => a.layer - b.layer);
  for (const n of sorted) {
    const id = `n-${n.neuron_id}`;
    if (nodeIds.has(id)) continue;
    const isConcept = n.layer === -1;
    const dept = n.department ?? 'Unknown';
    graph.addNode(id, {
      label: n.label || `#${n.neuron_id}`,
      x: Math.random() * 200 - 100,
      y: (n.layer >= 0 ? n.layer + 1 : 3) * 80,
      size: layerSize(n.layer) * (0.6 + (n.combined / maxScore) * 0.8),
      color: isConcept ? CONCEPT_COLOR : deptColor(dept),
      department: dept,
      layer: n.layer,
      neuron_id: n.neuron_id,
      combined: n.combined,
      spread_boost: n.spread_boost,
      burst: n.burst,
      impact: n.impact,
      precision: n.precision,
      novelty: n.novelty,
      recency: n.recency,
      relevance: n.relevance,
      summary: n.summary,
      borderColor: n.spread_boost > 0 ? SPREAD_RING_COLOR : undefined,
    });
    nodeIds.add(id);
  }

  // Trail nodes not in scores
  const trailNodes = spreadTrail?.nodes ?? [];
  for (const tn of trailNodes) {
    const id = `n-${tn.id}`;
    if (nodeIds.has(id)) continue;
    const isConcept = tn.layer === -1;
    const dept = tn.department ?? 'Concepts';
    graph.addNode(id, {
      label: tn.label || `#${tn.id}`,
      x: Math.random() * 200 - 100,
      y: (tn.layer >= 0 ? tn.layer + 1 : 3) * 80,
      size: layerSize(tn.layer) * 0.7,
      color: isConcept ? CONCEPT_COLOR : deptColor(dept),
      department: dept,
      layer: tn.layer,
      neuron_id: tn.id,
      combined: tn.combined,
      spread_boost: tn.spread_boost,
    });
    nodeIds.add(id);
  }

  // ── Deterministic hierarchical layout ──
  // Group nodes by layer (skip prompt)
  const layerGroups = new Map<number, string[]>();
  graph.forEachNode((key, attrs) => {
    if (attrs.isPrompt) return;
    const layer = attrs.layer as number;
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer)!.push(key);
  });

  const layerSpacing = 250;
  const scoreSpread = 150;

  for (const [layer, keys] of layerGroups) {
    // Sort by department then by score within department for spatial coherence
    keys.sort((a, b) => {
      const dA = graph.getNodeAttribute(a, 'department') as string;
      const dB = graph.getNodeAttribute(b, 'department') as string;
      if (dA !== dB) return dA.localeCompare(dB);
      return (graph.getNodeAttribute(b, 'combined') as number) - (graph.getNodeAttribute(a, 'combined') as number);
    });

    const bandY = -(layer >= 0 ? layer + 1 : 3) * layerSpacing; // negative = below prompt (top-down)
    const spreadWidth = Math.max(250, keys.length * 40);

    for (let i = 0; i < keys.length; i++) {
      const key = keys[i];
      const score = graph.getNodeAttribute(key, 'combined') as number;
      const scoreOffset = (1 - score / maxScore) * scoreSpread; // high score = closer to top of band
      const x = (i / Math.max(1, keys.length - 1) - 0.5) * spreadWidth;
      graph.setNodeAttribute(key, 'x', x);
      graph.setNodeAttribute(key, 'y', bandY - scoreOffset);
    }
  }

  // Prompt stays at origin (top of the tree)

  // Hierarchy edges: parent→child or prompt→child
  for (const n of sorted) {
    const id = `n-${n.neuron_id}`;
    const parentKey = n.parent_id != null ? `n-${n.parent_id}` : null;
    const source = parentKey && nodeIds.has(parentKey) ? parentKey : '__prompt__';
    const edgeKey = `h-${source}-${id}`;
    if (!graph.hasEdge(edgeKey)) {
      graph.addEdgeWithKey(edgeKey, source, id, {
        weight: 0.3,
        color: '#3b82f633',
        edgeKind: 'hierarchy',
        size: 0.5,
      });
    }
  }

  // Bridge node hierarchy edges
  if (ancestorData) {
    for (const [, anc] of ancestorData) {
      const id = `n-${anc.id}`;
      if (!nodeIds.has(id)) continue;
      const parentKey = anc.parent_id != null ? `n-${anc.parent_id}` : null;
      const source = parentKey && nodeIds.has(parentKey) ? parentKey : '__prompt__';
      const edgeKey = `h-${source}-${id}`;
      if (!graph.hasEdge(edgeKey)) {
        graph.addEdgeWithKey(edgeKey, source, id, {
          weight: 0.2,
          color: '#3b82f622',
          edgeKind: 'hierarchy',
          size: 0.3,
        });
      }
    }
  }

  // Spread trail edges (co-firing)
  const edges = spreadTrail?.edges ?? [];
  for (const e of edges) {
    const srcId = `n-${e.source_id}`;
    const tgtId = `n-${e.target_id}`;
    if (!nodeIds.has(srcId) || !nodeIds.has(tgtId)) continue;
    const edgeKey = `s-${e.source_id}-${e.target_id}`;
    if (!graph.hasEdge(edgeKey)) {
      const srcDept = graph.getNodeAttribute(srcId, 'department');
      graph.addEdgeWithKey(edgeKey, srcId, tgtId, {
        weight: e.weight,
        color: deptColor(srcDept, 0.4),
        edgeKind: 'cofiring',
        size: 0.8 + e.weight * 1.5,
        hidden: true, // hidden by default; revealed on node selection
      });
    }
  }

  return graph;
}

/** 3D graph API response shape */
export interface Graph3DNode {
  id: number;
  label: string;
  department: string | null;
  layer: number;
  node_type: string;
  invocations: number;
  avg_utility: number;
  parent_id: number | null;
}

export interface Graph3DEdge {
  source_id: number;
  target_id: number;
  weight: number;
  edge_type: string;
}

export interface Graph3DResponse {
  nodes: Graph3DNode[];
  edges: Graph3DEdge[];
}

/**
 * Convert the /neurons/graph3d response into a Graphology graph.
 * Used by the standalone SigmaGraphPage.
 */
export function graph3DToGraphology(data: Graph3DResponse): Graph {
  const graph = new Graph({ type: 'undirected', multi: true });
  const nodeIds = new Set<string>();

  // Build hierarchical initial positions: departments spread on X, layers on Y
  const departments = [...new Set(data.nodes.map(n => n.department ?? 'Concepts'))].sort();
  const deptIndex = new Map(departments.map((d, i) => [d, i]));
  const deptCount = departments.length || 1;

  // Group nodes by department+layer for spacing
  const deptLayerCounts = new Map<string, number>();
  const deptLayerSeen = new Map<string, number>();
  for (const n of data.nodes) {
    const key = `${n.department ?? 'Concepts'}|${n.layer}`;
    deptLayerCounts.set(key, (deptLayerCounts.get(key) ?? 0) + 1);
    deptLayerSeen.set(key, 0);
  }

  const layerSpacing = 200;
  const deptSpread = 300;

  for (const n of data.nodes) {
    const id = `n-${n.id}`;
    const isConcept = n.layer === -1;
    const dept = n.department ?? 'Concepts';
    const di = deptIndex.get(dept) ?? 0;
    const key = `${dept}|${n.layer}`;
    const idx = deptLayerSeen.get(key) ?? 0;
    deptLayerSeen.set(key, idx + 1);
    const count = deptLayerCounts.get(key) ?? 1;

    // X: department arc position + spread within department
    const deptAngle = (di / deptCount) * 2 * Math.PI;
    const deptCenterX = Math.cos(deptAngle) * deptSpread;
    const deptCenterY = Math.sin(deptAngle) * deptSpread;
    // Offset within dept-layer group
    const withinSpread = Math.min(80, 200 / Math.max(1, count));
    const offsetX = (idx - count / 2) * withinSpread * 0.3;
    const offsetY = n.layer * layerSpacing * 0.15;

    graph.addNode(id, {
      label: n.label,
      x: deptCenterX + offsetX + (Math.random() - 0.5) * 20,
      y: deptCenterY + offsetY + (Math.random() - 0.5) * 20,
      size: layerSize(n.layer),
      color: isConcept ? CONCEPT_COLOR : deptColor(dept),
      department: dept,
      layer: n.layer,
      neuron_id: n.id,
      node_type: n.node_type,
      invocations: n.invocations,
      avg_utility: n.avg_utility,
      parent_id: n.parent_id,
    });
    nodeIds.add(id);
  }

  // Hierarchy edges (parent→child) — these give FA2 structural pull
  for (const n of data.nodes) {
    if (n.parent_id == null) continue;
    const childId = `n-${n.id}`;
    const parentId = `n-${n.parent_id}`;
    if (!nodeIds.has(parentId)) continue;
    const edgeKey = `h-${n.parent_id}-${n.id}`;
    if (graph.hasEdge(edgeKey)) continue;
    graph.addEdgeWithKey(edgeKey, parentId, childId, {
      weight: 1.5,
      color: '#3b82f618',
      edgeKind: 'hierarchy',
      size: 0.3,
    });
  }

  // Co-firing / stellate edges
  for (const e of data.edges) {
    const srcId = `n-${e.source_id}`;
    const tgtId = `n-${e.target_id}`;
    if (!nodeIds.has(srcId) || !nodeIds.has(tgtId)) continue;
    const edgeKey = `e-${e.source_id}-${e.target_id}`;
    if (graph.hasEdge(edgeKey)) continue;
    const isStellate = e.edge_type === 'stellate';
    const srcDept = graph.getNodeAttribute(srcId, 'department');
    graph.addEdgeWithKey(edgeKey, srcId, tgtId, {
      weight: e.weight,
      color: isStellate ? deptColor(srcDept, 0.3) : '#94a3b844',
      edgeKind: e.edge_type,
      size: 0.5 + e.weight * 2,
    });
  }

  return graph;
}
