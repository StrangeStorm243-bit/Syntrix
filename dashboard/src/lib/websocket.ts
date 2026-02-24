export type WsMessage =
  | { type: 'pipeline_progress'; stage: string; progress: number; detail: string }
  | { type: 'queue_update'; action: string; draft_id: number }
  | { type: 'new_lead'; lead_id: number; score: number };

type Listener = (msg: WsMessage) => void;

export class SignalOpsWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Listener[] = [];
  private reconnectDelay = 1000;
  private maxDelay = 30000;
  private shouldConnect = false;

  connect(): void {
    this.shouldConnect = true;
    this._connect();
  }

  disconnect(): void {
    this.shouldConnect = false;
    this.ws?.close();
    this.ws = null;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private _connect(): void {
    if (!this.shouldConnect) return;
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${proto}//${window.location.host}/ws/pipeline`);

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data) as WsMessage;
      this.listeners.forEach((l) => l(msg));
    };

    this.ws.onclose = () => {
      if (!this.shouldConnect) return;
      setTimeout(() => this._connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
    };

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
    };
  }
}

export const wsClient = new SignalOpsWebSocket();
