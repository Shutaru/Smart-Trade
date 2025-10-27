import { useEffect, useRef } from 'react';

export const useWS = (url: string, onMessage: (data: any) => void) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url);

      ws.current.onmessage = (event) => {
        onMessage(JSON.parse(event.data));
      };

      ws.current.onclose = () => {
        setTimeout(connect, 1000); // Exponential backoff can be added here
      };
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url, onMessage]);
};
