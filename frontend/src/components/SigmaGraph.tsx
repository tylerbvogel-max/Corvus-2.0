/**
 * Shared Sigma.js + Graphology wrapper component.
 * Handles initialization, cleanup, resize, ForceAtlas2 layout, hover tooltips,
 * and click-to-select with neighbor highlighting.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import Sigma from 'sigma';
import Graph from 'graphology';
import FA2Layout from 'graphology-layout-forceatlas2/worker';

const LAYER_LABELS = ['Dept', 'Role', 'Task', 'System', 'Decision', 'Output'];

interface SigmaGraphProps {
  graph: Graph;
  height?: string | number;
  onNodeClick?: (nodeKey: string, attrs: Record<string, unknown>) => void;
  onNodeHover?: (nodeKey: string | null, attrs: Record<string, unknown> | null) => void;
  autoLayout?: boolean;
  layoutSettings?: {
    gravity?: number;
    scalingRatio?: number;
  };
}

export default function SigmaGraph({
  graph,
  height = '100%',
  onNodeClick,
  onNodeHover,
  autoLayout = true,
  layoutSettings,
}: SigmaGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const layoutRef = useRef<FA2Layout | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [tooltipData, setTooltipData] = useState<{ x: number; y: number; attrs: Record<string, unknown> } | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Track when the container has actual pixel dimensions (needed for Sigma init).
  // When SigmaGraph mounts inside a Section that just opened, the container
  // may report 0x0 on the first frame. The ResizeObserver fires once the
  // browser paints real dimensions, flipping this flag and re-triggering init.
  const [containerReady, setContainerReady] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        const h = entry.contentRect.height;
        if (w > 0 && h > 0) {
          setContainerReady(true);
        }
      }
      sigmaRef.current?.refresh();
    });
    ro.observe(el);
    return () => { ro.disconnect(); setContainerReady(false); };
  }, []);

  // Initialize Sigma once container is ready and graph has nodes
  useEffect(() => {
    if (!containerRef.current || !containerReady || graph.order === 0) {
      return;
    }

    let sigma: Sigma;
    let layout: FA2Layout | null = null;
    let stopTimer: ReturnType<typeof setTimeout> | null = null;

    try {
      sigma = new Sigma(graph, containerRef.current, {
        renderLabels: true,
        labelRenderedSizeThreshold: 14,
        labelSize: 10,
        labelWeight: 'bold',
        labelColor: { color: '#e2e8f0' },
        defaultEdgeColor: '#3b82f633',
        defaultNodeColor: '#4a5568',
        minCameraRatio: 0.05,
        maxCameraRatio: 10,
      });
    } catch (err) {
      console.error('[SigmaGraph] Failed to initialize Sigma:', err);
      return;
    }

    sigmaRef.current = sigma;

    // Node reducer for selection/hover highlighting
    sigma.setSetting('nodeReducer', (node, data) => {
      const res = { ...data };
      if (selectedNode) {
        if (node === selectedNode) {
          res.highlighted = true;
          res.zIndex = 2;
        } else if (graph.areNeighbors(selectedNode, node)) {
          res.zIndex = 1;
        } else {
          res.color = (res.color as string || '#4a5568') + '33';
          res.label = '';
          res.zIndex = 0;
        }
      }
      if (node === hoveredNode) {
        res.highlighted = true;
        res.zIndex = 3;
      }
      return res;
    });

    sigma.setSetting('edgeReducer', (edge, data) => {
      const res = { ...data };
      if (selectedNode) {
        const [src, tgt] = graph.extremities(edge);
        if (src === selectedNode || tgt === selectedNode) {
          // Show all edges touching the selected node, including cofiring
          res.hidden = false;
        } else {
          res.hidden = true;
        }
      }
      // When no node selected, cofiring edges stay hidden (set in graph data)
      return res;
    });

    // Event handlers
    sigma.on('enterNode', ({ node }) => {
      setHoveredNode(node);
      const attrs = graph.getNodeAttributes(node);
      const displayData = sigma.getNodeDisplayData(node);
      if (displayData) {
        const viewportPos = sigma.graphToViewport(displayData);
        setTooltipData({ x: viewportPos.x, y: viewportPos.y, attrs });
      }
      onNodeHover?.(node, attrs);
    });

    sigma.on('leaveNode', () => {
      setHoveredNode(null);
      setTooltipData(null);
      onNodeHover?.(null, null);
    });

    sigma.on('clickNode', ({ node }) => {
      setSelectedNode(prev => prev === node ? null : node);
      const attrs = graph.getNodeAttributes(node);
      onNodeClick?.(node, attrs);
    });

    sigma.on('clickStage', () => {
      setSelectedNode(null);
    });

    // Start ForceAtlas2 layout
    if (autoLayout && graph.order > 1) {
      const nodeCount = graph.order;
      const gravity = layoutSettings?.gravity ?? (nodeCount < 500 ? 0.8 : nodeCount < 2000 ? 0.5 : 0.3);
      const scalingRatio = layoutSettings?.scalingRatio ?? (nodeCount < 500 ? 15 : nodeCount < 2000 ? 30 : 60);

      try {
        layout = new FA2Layout(graph, {
          settings: {
            gravity,
            scalingRatio,
            barnesHutOptimize: nodeCount > 500,
            slowDown: 5,
            strongGravityMode: false,
          },
        });
        layoutRef.current = layout;
        layout.start();

        stopTimer = setTimeout(() => {
          if (layout?.isRunning()) layout.stop();
        }, nodeCount < 500 ? 5000 : 10000);
      } catch (err) {
        console.error('[SigmaGraph] Failed to start FA2 layout:', err);
      }
    }

    return () => {
      if (stopTimer) clearTimeout(stopTimer);
      if (layout) {
        if (layout.isRunning()) layout.stop();
        layout.kill();
      }
      sigma.kill();
      sigmaRef.current = null;
      layoutRef.current = null;
    };
  }, [graph, containerReady]);  // eslint-disable-line react-hooks/exhaustive-deps

  // Zoom controls
  const zoomIn = useCallback(() => {
    const camera = sigmaRef.current?.getCamera();
    if (camera) camera.animatedZoom({ duration: 300 });
  }, []);

  const zoomOut = useCallback(() => {
    const camera = sigmaRef.current?.getCamera();
    if (camera) camera.animatedUnzoom({ duration: 300 });
  }, []);

  const zoomFit = useCallback(() => {
    const camera = sigmaRef.current?.getCamera();
    if (camera) camera.animatedReset({ duration: 300 });
  }, []);

  const toggleLayout = useCallback(() => {
    const layout = layoutRef.current;
    if (!layout) return;
    if (layout.isRunning()) {
      layout.stop();
    } else {
      layout.start();
      setTimeout(() => { if (layout.isRunning()) layout.stop(); }, 5000);
    }
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height, minHeight: 200 }}>
      <div
        ref={containerRef}
        style={{ width: '100%', height: '100%', background: 'rgba(0,0,0,0.15)', borderRadius: 8 }}
      />

      {/* Zoom controls */}
      <div style={{
        position: 'absolute', top: 8, right: 8,
        display: 'flex', flexDirection: 'column', gap: 4, zIndex: 10,
      }}>
        {[
          { label: '+', onClick: zoomIn, title: 'Zoom in' },
          { label: '-', onClick: zoomOut, title: 'Zoom out' },
          { label: '\u22a1', onClick: zoomFit, title: 'Fit to screen' },
          ...(autoLayout ? [{ label: '\u27f3', onClick: toggleLayout, title: 'Toggle layout' }] : []),
        ].map(btn => (
          <button
            key={btn.label}
            onClick={btn.onClick}
            title={btn.title}
            style={{
              width: 28, height: 28, borderRadius: 4,
              background: 'rgba(30, 41, 59, 0.85)',
              border: '1px solid rgba(100, 116, 139, 0.3)',
              color: '#e2e8f0', fontSize: 14, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Hover tooltip */}
      {tooltipData && (
        <div style={{
          position: 'absolute',
          left: tooltipData.x + 15,
          top: tooltipData.y - 10,
          background: 'rgba(15, 23, 42, 0.95)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: 6,
          padding: '6px 10px',
          fontSize: '0.75rem',
          color: '#e2e8f0',
          pointerEvents: 'none',
          zIndex: 20,
          maxWidth: 260,
          backdropFilter: 'blur(8px)',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 2 }}>{String(tooltipData.attrs.label ?? '')}</div>
          <div style={{ color: String(tooltipData.attrs.color ?? '#94a3b8'), fontSize: '0.7rem' }}>
            {tooltipData.attrs.layer === -1 ? 'Concept' : String(tooltipData.attrs.department ?? '')}
            {' \u00b7 '}
            {tooltipData.attrs.layer === -1 ? 'Concept' : (LAYER_LABELS[Number(tooltipData.attrs.layer)] ?? `L${tooltipData.attrs.layer}`)}
          </div>
          {tooltipData.attrs.combined != null && Number(tooltipData.attrs.combined) > 0 && (
            <div style={{ marginTop: 2, fontSize: '0.68rem', color: '#94a3b8' }}>
              Score: {Number(tooltipData.attrs.combined).toFixed(3)}
              {Number(tooltipData.attrs.spread_boost) > 0 && (
                <span style={{ color: '#e8a735' }}> +{Number(tooltipData.attrs.spread_boost).toFixed(3)} spread</span>
              )}
            </div>
          )}
          {typeof tooltipData.attrs.summary === 'string' && tooltipData.attrs.summary && (
            <div style={{ marginTop: 2, fontSize: '0.65rem', color: '#64748b', maxWidth: 240 }}>
              {tooltipData.attrs.summary.slice(0, 120)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
