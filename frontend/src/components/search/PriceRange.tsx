"use client";

import { formatINR } from "@/lib/format";
import type { PriceHistogram } from "@/types/api";

const STEP = 100;

type Props = {
  histogram: PriceHistogram | null;
  min?: number;
  max?: number;
  onChange: (min?: number, max?: number) => void;
};

/** A histogram of nightly prices over a two-handle slider, with min / max fields beneath. */
export function PriceRange({ histogram, min, max, onChange }: Props) {
  const low = histogram ? Math.floor(histogram.min_price / STEP) * STEP : 0;
  const high = histogram ? Math.max(Math.ceil(histogram.max_price / STEP) * STEP, low + STEP) : STEP;
  const from = Math.min(Math.max(min ?? low, low), high);
  const to = Math.max(Math.min(max ?? high, high), low);
  const peak = Math.max(1, ...(histogram?.buckets ?? []));
  const bucketCount = histogram?.buckets.length ?? 0;
  const pct = (value: number) => ((value - low) / (high - low)) * 100;

  // A handle sitting on the end of the range means "no limit on that side".
  const commit = (nextFrom: number, nextTo: number) => onChange(nextFrom <= low ? undefined : nextFrom, nextTo >= high ? undefined : nextTo);

  const field = "w-full rounded-control border border-line px-3 py-2 text-base focus:border-ink focus:outline-none";
  return (
    <div>
      <div className="relative h-16" aria-hidden>
        <div className="absolute inset-x-0 bottom-0 flex h-16 items-end gap-px">
          {histogram?.buckets.map((count, i) => {
            const start = low + ((high - low) * i) / bucketCount;
            const end = low + ((high - low) * (i + 1)) / bucketCount;
            const inside = end > from && start < to;
            return (
              <div
                key={i}
                style={{ height: `${Math.max(4, (count / peak) * 100)}%` }}
                className={`flex-1 rounded-t-sm ${inside ? "bg-[#b0b0b0]" : "bg-line-soft"}`}
              />
            );
          })}
        </div>
      </div>
      <div className="relative mx-4 h-8">
        <div className="absolute inset-x-0 top-1/2 h-0.5 -translate-y-1/2 bg-line" />
        <div className="absolute top-1/2 h-0.5 -translate-y-1/2 bg-ink" style={{ left: `${pct(from)}%`, right: `${100 - pct(to)}%` }} />
        {[
          { label: "Minimum price", value: from, onInput: (v: number) => commit(Math.min(v, to - STEP), to) },
          { label: "Maximum price", value: to, onInput: (v: number) => commit(from, Math.max(v, from + STEP)) },
        ].map((slider) => (
          <input
            key={slider.label}
            type="range"
            aria-label={slider.label}
            min={low}
            max={high}
            step={STEP}
            value={slider.value}
            onChange={(event) => slider.onInput(Number(event.target.value))}
            className="dual-range absolute -inset-x-4 top-0 h-8 w-[calc(100%+2rem)]"
          />
        ))}
      </div>
      <div className="mt-4 flex items-center gap-4">
        <label className="flex-1">
          <span className="mb-1 block text-xs text-muted">Minimum</span>
          <input
            inputMode="numeric"
            aria-label="Minimum price in rupees"
            className={field}
            value={min ?? ""}
            placeholder={formatINR(low)}
            onChange={(event) => onChange(Number(event.target.value.replace(/\D/g, "")) || undefined, max)}
          />
        </label>
        <span className="mt-5 text-muted">–</span>
        <label className="flex-1">
          <span className="mb-1 block text-xs text-muted">Maximum</span>
          <input
            inputMode="numeric"
            aria-label="Maximum price in rupees"
            className={field}
            value={max ?? ""}
            placeholder={`${formatINR(high)}+`}
            onChange={(event) => onChange(min, Number(event.target.value.replace(/\D/g, "")) || undefined)}
          />
        </label>
      </div>
    </div>
  );
}
