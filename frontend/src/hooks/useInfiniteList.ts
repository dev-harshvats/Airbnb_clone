"use client";

import { useEffect, useRef, useState } from "react";

type PageResult<T> = { items: T[]; total: number };
type State<T> = { key: string; items: T[]; total: number; page: number; loading: boolean; failed: boolean };

/**
 * Loads a paged list and keeps loading as the returned sentinel scrolls into view.
 * `key` identifies the search (usually the URL); changing it starts again from page one, and a slow
 * response for an old key is ignored. `fetchPage` must return the same results for the same key.
 */
export function useInfiniteList<T>(key: string, fetchPage: (page: number) => Promise<PageResult<T>>) {
  const [state, setState] = useState<State<T>>({ key: "", items: [], total: 0, page: 0, loading: true, failed: false });
  // A callback ref: the element that, when scrolled into view, triggers the next page.
  const [sentinel, setSentinel] = useState<HTMLDivElement | null>(null);
  const fetchRef = useRef(fetchPage);
  useEffect(() => {
    fetchRef.current = fetchPage;
  });

  // First page for this key.
  useEffect(() => {
    let current = true;
    fetchRef
      .current(1)
      .then((result) => {
        if (current) setState({ key, items: result.items, total: result.total, page: 1, loading: false, failed: false });
      })
      .catch(() => {
        if (current) setState((s) => ({ ...s, key, loading: false, failed: true }));
      });
    return () => {
      current = false;
    };
  }, [key]);

  // Results that belong to an older key are treated as "still loading".
  const stale = state.key !== key;
  const items = stale ? [] : state.items;
  const hasMore = !stale && items.length < state.total;

  useEffect(() => {
    if (!sentinel || !hasMore || state.loading) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        const next = state.page + 1;
        setState((s) => ({ ...s, loading: true }));
        // A page that arrives after the search changed belongs to the old search: drop it.
        fetchRef
          .current(next)
          .then((result) =>
            setState((s) => (s.key !== key ? s : { ...s, items: [...s.items, ...result.items], total: result.total, page: next, loading: false })),
          )
          .catch(() => setState((s) => (s.key !== key ? s : { ...s, loading: false, failed: true })));
      },
      { rootMargin: "400px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [sentinel, hasMore, state.loading, state.page, key]);

  return {
    items,
    total: state.total,
    loading: stale || state.loading,
    firstLoad: stale || (state.loading && items.length === 0),
    failed: state.failed && items.length === 0,
    setSentinel,
  };
}
