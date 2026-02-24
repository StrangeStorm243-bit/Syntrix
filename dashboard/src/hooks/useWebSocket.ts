import { useEffect, useState } from 'react';
import { wsClient, type WsMessage } from '../lib/websocket';

export function useWebSocket(): { lastMessage: WsMessage | null; connected: boolean } {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    wsClient.connect();
    setConnected(true);
    const unsub = wsClient.subscribe((msg) => setLastMessage(msg));
    return () => {
      unsub();
      wsClient.disconnect();
      setConnected(false);
    };
  }, []);

  return { lastMessage, connected };
}
