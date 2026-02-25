import ELK from 'elkjs/lib/elk.bundled.js';
import type { PipelineStage } from './types';

const elk = new ELK();

export interface LayoutNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface LayoutEdgeSection {
  startPoint: { x: number; y: number };
  endPoint: { x: number; y: number };
  bendPoints?: Array<{ x: number; y: number }>;
}

export interface LayoutEdge {
  id: string;
  sections: LayoutEdgeSection[];
}

export interface LayoutResult {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
}

const NODE_WIDTH = 160;
const NODE_HEIGHT = 120;

export async function computeLayout(stages: PipelineStage[]): Promise<LayoutResult> {
  const elkNodes = stages.map((stage) => ({
    id: stage.id,
    width: NODE_WIDTH,
    height: NODE_HEIGHT,
  }));

  const elkEdges = stages.slice(0, -1).map((stage, i) => ({
    id: `e-${stage.id}-${stages[i + 1].id}`,
    sources: [stage.id],
    targets: [stages[i + 1].id],
  }));

  const graph = {
    id: 'pipeline-root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.spacing.nodeNode': '80',
      'elk.layered.spacing.nodeNodeBetweenLayers': '120',
      'elk.layered.nodePlacement.strategy': 'SIMPLE',
      'elk.edgeRouting': 'POLYLINE',
    },
    children: elkNodes,
    edges: elkEdges,
  };

  const layout = await elk.layout(graph);

  const nodes: LayoutNode[] = (layout.children ?? []).map((n) => ({
    id: n.id,
    x: n.x ?? 0,
    y: n.y ?? 0,
    width: n.width ?? NODE_WIDTH,
    height: n.height ?? NODE_HEIGHT,
  }));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const edges: LayoutEdge[] = (layout.edges ?? []).map((e: any) => ({
    id: e.id,
    sections: (e.sections ?? []).map((s: any) => ({
      startPoint: s.startPoint,
      endPoint: s.endPoint,
      bendPoints: s.bendPoints,
    })),
  }));

  return { nodes, edges };
}
