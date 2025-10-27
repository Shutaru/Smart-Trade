import { useEffect, useRef } from 'react';

type UsePollingOptions = {
  interval: number;
  enabled?: boolean;
};

export function usePolling(callback: () => void, { interval, enabled = true }: UsePollingOptions) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const id = window.setInterval(() => {
      callbackRef.current();
    }, interval);

    return () => window.clearInterval(id);
  }, [enabled, interval]);
}
