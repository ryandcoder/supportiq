import { useEffect, useState } from "react";

/** Runs `fetcher` whenever `deps` change. Ignores responses that arrive after a newer request started. */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    fetcher()
      .then((d) => {
        if (!stale) {
          setData(d);
          setError(null);
        }
      })
      .catch((e) => {
        if (!stale) setError(e?.response?.data?.detail ?? e?.message ?? "Request failed");
      })
      .finally(() => {
        if (!stale) setLoading(false);
      });
    return () => {
      stale = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}

/** Value that only updates after `delay` ms without changes (used for the search box). */
export function useDebounced<T>(value: T, delay = 300): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return v;
}
