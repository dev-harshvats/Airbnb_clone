"use client";

import { useSyncExternalStore } from "react";

/** The header folds up once you scroll past this, and unfolds again near the top (a gap, so it never flickers). */
const COLLAPSE_AFTER = 24;
const EXPAND_BELOW = 8;

let collapsed = false;

function read() {
  const y = window.scrollY;
  if (collapsed ? y < EXPAND_BELOW : y > COLLAPSE_AFTER) collapsed = !collapsed;
  return collapsed;
}

function subscribe(listener: () => void) {
  let frame = 0;
  const onScroll = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(listener);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  return () => {
    window.removeEventListener("scroll", onScroll);
    cancelAnimationFrame(frame);
  };
}

/** True once the page has been scrolled down a little. Rendered as "not scrolled" on the server. */
export function useScrollCollapsed(): boolean {
  return useSyncExternalStore(subscribe, read, () => false);
}
