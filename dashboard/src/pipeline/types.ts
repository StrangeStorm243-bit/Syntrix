export interface PipelineStage {
  id: string;
  label: string;
  count: number;
  active: boolean;
  color: string;
}

export interface PipelineEdge {
  source: string;
  target: string;
  throughput: number;
  animated: boolean;
}

export interface PipelineEvent {
  id: string;
  type: 'item_entered' | 'item_completed' | 'item_failed';
  stage: string;
  timestamp: number;
  detail: string;
}

export interface PipelineFlowData {
  stages: PipelineStage[];
  edges: PipelineEdge[];
  events: PipelineEvent[];
  isLive: boolean;
}
