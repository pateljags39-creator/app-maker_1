import { useCallback, useEffect, useState } from 'react';
import api from './api';

export function useProject(id) {
  const [project, setProject] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    if (!id) return;
    try {
      const p = await api.getProject(id);
      setProject(p);
      setError(null);
    } catch (e) {
      setError(e);
    }
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  // Periodic poll for state updates so cockpit reflects pipeline transitions.
  useEffect(() => {
    if (!id) return undefined;
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [id, refresh]);

  return { project, refresh, error };
}

export default useProject;
