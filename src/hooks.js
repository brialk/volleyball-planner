import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Runs an async function and tracks { data, loading, error } for it.
 * Call reload() to run it again. Old responses are ignored, so a slow
 * request can never overwrite a newer one.
 */
export function useLoad(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  const requestId = useRef(0);

  const run = useCallback(() => {
    const id = ++requestId.current;
    setState((current) => ({ ...current, loading: true, error: "" }));
    loader()
      .then((data) => {
        if (id === requestId.current) setState({ data, loading: false, error: "" });
      })
      .catch((error) => {
        if (id === requestId.current) setState({ data: null, loading: false, error: error.message });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    run();
    return () => {
      requestId.current += 1; // ignore the result if the page was left
    };
  }, [run]);

  return { ...state, reload: run, setData: (data) => setState((current) => ({ ...current, data })) };
}

/** Returns value after it has stopped changing for delay ms. Used for search boxes. */
export function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
