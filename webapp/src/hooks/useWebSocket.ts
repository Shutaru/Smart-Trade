import { useEffect, useRef, useState } from 'react';

type Options<TMessage> = {
  onMessage?: (data: TMessage) => void;
  enabled?: boolean;
  parser?: (event: MessageEvent) => TMessage;
  reconnectAttempts?: number;
};

type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

const defaultParser = <TMessage,>(event: MessageEvent): TMessage => JSON.parse(event.data) as TMessage;

export function useWebSocket<TMessage = unknown>(url: string, options: Options<TMessage> = {}) {
  const { onMessage, enabled = true, parser = defaultParser, reconnectAttempts = 5 } = options;
  const [status, setStatus] = useState<WebSocketStatus>('closed');
  const reconnectRef = useRef(0);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    let cancelled = false;

    const connect = () => {
      if (cancelled) {
        return;
      }
      const ws = new WebSocket(url);
      socketRef.current = ws;
      setStatus('connecting');

      ws.onopen = () => {
        reconnectRef.current = 0;
        setStatus('open');
      };

      ws.onmessage = (event) => {
        if (onMessage) {
          try {
            onMessage(parser(event));
          } catch (error) {
            console.warn('WebSocket message parse failed', error);
          }
        }
      };

      ws.onerror = () => {
        setStatus('error');
      };

      ws.onclose = () => {
        setStatus('closed');
        socketRef.current = null;
        if (reconnectRef.current < reconnectAttempts) {
          reconnectRef.current += 1;
          const timeout = Math.min(10_000, 1000 * 2 ** reconnectRef.current);
          window.setTimeout(connect, timeout);
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      socketRef.current?.close();
    };
  }, [enabled, onMessage, parser, reconnectAttempts, url]);

  return { status } as const;
}
