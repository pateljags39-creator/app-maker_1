import { useEffect, useRef, useState } from 'react';

/**
 * useEventStream — connects to a server-sent events endpoint.
 * Returns: { events, status }
 *   - status: 'idle' | 'connecting' | 'open' | 'closed' | 'error'
 */
export function useEventStream(url, { enabled = true, max = 200 } = {}) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('idle');
  const esRef = useRef(null);

  useEffect(() => {
    if (!enabled || !url) return undefined;
    setStatus('connecting');
    const es = new EventSource(url);
    esRef.current = es;

    const onEvent = (e) => {
      try {
        const payload = JSON.parse(e.data);
        setEvents(prev => {
          const next = [payload, ...prev];
          return next.length > max ? next.slice(0, max) : next;
        });
      } catch (_) { /* ignore parse */ }
    };

    const onHello = (_e) => {
      setStatus('open');
    };

    es.addEventListener('event', onEvent);
    es.addEventListener('hello', onHello);
    es.onopen = () => setStatus('open');
    es.onerror = () => {
      setStatus('error');
      // EventSource will auto-reconnect.
    };

    return () => {
      es.removeEventListener('event', onEvent);
      es.removeEventListener('hello', onHello);
      es.close();
      setStatus('closed');
    };
  }, [url, enabled, max]);

  const clear = () => setEvents([]);

  return { events, status, clear };
}

export default useEventStream;
