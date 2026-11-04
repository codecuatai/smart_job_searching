'use client';
import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
export function useResource<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => setVersion(v => v + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    api<T>(path, { signal: controller.signal }).then(setData).catch(err => {
      if (err.name !== 'AbortError') setError(err.message);
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, version]);
  return { data, error, loading, reload };
}
