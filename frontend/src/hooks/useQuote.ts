"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { listingsApi } from "@/lib/api/listings";
import type { Quote } from "@/types/api";

type Settled = { key: string; quote: Quote | null; error: string | null };

/**
 * The server-computed price for a stay (the browser never does price arithmetic). Nothing is fetched
 * until both dates are chosen; a rule the stay breaks (minimum nights, past date...) arrives as `error`.
 */
export function useQuote(listingId: number | string, checkIn?: string, checkOut?: string) {
  const key = checkIn && checkOut ? `${listingId}|${checkIn}|${checkOut}` : "";
  const [settled, setSettled] = useState<Settled>({ key: "", quote: null, error: null });

  useEffect(() => {
    if (!key || !checkIn || !checkOut) return;
    let current = true;
    listingsApi
      .quote(listingId, checkIn, checkOut)
      .then((quote) => current && setSettled({ key, quote, error: null }))
      .catch((error) => current && setSettled({ key, quote: null, error: error instanceof ApiError ? error.detail : "Could not price this stay." }));
    return () => {
      current = false;
    };
  }, [key, listingId, checkIn, checkOut]);

  if (!key) return { quote: null, loading: false, error: null };
  if (settled.key !== key) return { quote: null, loading: true, error: null };
  return { quote: settled.quote, loading: false, error: settled.error };
}
