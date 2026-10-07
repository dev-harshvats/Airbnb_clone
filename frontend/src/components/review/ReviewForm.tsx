"use client";

import { Star } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { bookingsApi, type ReviewInput } from "@/lib/api/bookings";

const CATEGORIES: [key: keyof Omit<ReviewInput, "comment">, label: string][] = [
  ["cleanliness", "Cleanliness"],
  ["accuracy", "Accuracy"],
  ["check_in", "Check-in"],
  ["communication", "Communication"],
  ["location", "Location"],
  ["value", "Value"],
];

function StarInput({ label, value, onChange }: { label: string; value: number; onChange: (n: number) => void }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <span className="font-medium">{label}</span>
      <div role="radiogroup" aria-label={label} className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} star${n === 1 ? "" : "s"}`}
            onClick={() => onChange(n)}
            className="p-0.5"
          >
            <Star size={26} className={n <= value ? "fill-ink stroke-ink" : "stroke-[#b0b0b0]"} />
          </button>
        ))}
      </div>
    </div>
  );
}

/** Six category ratings plus a comment, shown once a stay is over and not yet reviewed. */
export function ReviewForm({ code, onDone }: { code: string; onDone: () => void }) {
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const complete = CATEGORIES.every(([key]) => ratings[key]) && comment.trim().length > 0;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!complete) return;
    setBusy(true);
    try {
      await bookingsApi.review(code, { ...(ratings as Omit<ReviewInput, "comment">), comment: comment.trim() });
      toast.success("Thanks for your review");
      onDone();
    } catch (error) {
      setBusy(false);
      toast.error(error instanceof ApiError ? error.detail : "We couldn't save your review.");
    }
  };

  return (
    <form onSubmit={submit} className="p-6">
      <div className="divide-y divide-line-soft">
        {CATEGORIES.map(([key, label]) => (
          <StarInput key={key} label={label} value={ratings[key] ?? 0} onChange={(n) => setRatings((r) => ({ ...r, [key]: n }))} />
        ))}
      </div>
      <label className="mt-5 block">
        <span className="mb-2 block font-semibold">Tell future guests about your stay</span>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          maxLength={2000}
          rows={5}
          className="w-full rounded-control border border-muted p-3 focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
        />
      </label>
      <div className="mt-5 flex justify-end">
        <Button type="submit" variant="dark" size="lg" disabled={!complete} loading={busy}>
          Submit review
        </Button>
      </div>
    </form>
  );
}
