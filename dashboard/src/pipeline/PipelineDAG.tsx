import { useCallback, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { StageNode } from './StageNode';
import { DataEdge } from './DataEdge';
import { computeLayout } from './pipeline-layout';
import type { PipelineFlowData, PipelineStage } from './types';

// Memoize outside component to prevent re-registration on every render
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes: Record<string, any> = { stage: StageNode };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const edgeTypes: Record<string, any> = { data: DataEdge };

interface PipelineDAGProps {
  data: PipelineFlowData;
}

function stageToNode(stage: PipelineStage, x: number, y: number): Node {
  return {
    id: stage.id,
    type: 'stage',
    position: { x, y },
    data: { ...stage },
    draggable: false,
    selectable: false,
  };
}

export function PipelineDAG({ data }: PipelineDAGProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const runLayout = useCallback(
    async (stages: PipelineFlowData['stages'], pipelineEdges: PipelineFlowData['edges']) => {
      if (stages.length === 0) return;

      try {
        const layout = await computeLayout(stages);

        const positionMap = new Map(layout.nodes.map((n) => [n.id, n]));

        const flowNodes: Node[] = stages.map((stage) => {
          const pos = positionMap.get(stage.id);
          return stageToNode(stage, pos?.x ?? 0, pos?.y ?? 0);
        });

        const flowEdges: Edge[] = pipelineEdges.map((e) => ({
          id: `e-${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          type: 'data',
          animated: e.animated,
          data: { throughput: e.throughput },
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
      } catch (err) {
        // Fallback: linear horizontal layout if ELK fails
        const flowNodes: Node[] = stages.map((stage, i) =>
          stageToNode(stage, i * 280, 0),
        );
        const flowEdges: Edge[] = pipelineEdges.map((e) => ({
          id: `e-${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          type: 'data',
          animated: e.animated,
          data: { throughput: e.throughput },
        }));
        setNodes(flowNodes);
        setEdges(flowEdges);
        console.warn('[PipelineDAG] ELK layout failed, using fallback:', err);
      }
    },
    [setNodes, setEdges],
  );

  // Re-run layout when stage count changes (not on every data tick)
  const stageCount = data.stages.length;
  useEffect(() => {
    void runLayout(data.stages, data.edges);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stageCount]);

  // Update node data (counts, active state) without re-running layout
  useEffect(() => {
    setNodes((prev) =>
      prev.map((node) => {
        const updated = data.stages.find((s) => s.id === node.id);
        if (!updated) return node;
        return { ...node, data: { ...updated } };
      }),
    );
  }, [data.stages, setNodes]);

  // Update edge data (throughput) without re-running layout
  useEffect(() => {
    setEdges((prev) =>
      prev.map((edge) => {
        const updated = data.edges.find(
          (e) => e.source === edge.source && e.target === edge.target,
        );
        if (!updated) return edge;
        return { ...edge, data: { throughput: updated.throughput } };
      }),
    );
  }, [data.edges, setEdges]);

  const miniMapNodeColor = useCallback((node: Node) => {
    const stage = data.stages.find((s) => s.id === node.id);
    return stage?.color ?? '#ff1493';
  }, [data.stages]);

  const proOptions = useMemo(() => ({ hideAttribution: true }), []);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: 'var(--cyber-void)',
        position: 'relative',
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={proOptions}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnScroll
        zoomOnScroll
        style={{ background: 'transparent' }}
      >
        <MiniMap
          nodeColor={miniMapNodeColor}
          maskColor="rgba(10, 6, 8, 0.7)"
          style={{
            background: 'var(--cyber-surface)',
            border: '1px solid rgba(255, 20, 147, 0.2)',
            borderRadius: 4,
          }}
          nodeStrokeWidth={2}
        />
        <Controls
          style={{
            background: 'var(--cyber-surface)',
            border: '1px solid rgba(255, 20, 147, 0.2)',
            borderRadius: 4,
          }}
        />
      </ReactFlow>
    </div>
  );
}
