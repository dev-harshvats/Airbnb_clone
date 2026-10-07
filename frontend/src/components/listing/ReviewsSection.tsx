"use client";

import { Star } from "lucide-react";
import { useEffect, useState } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { listingsApi } from "@/lib/api/listings";
import type { ListingDetail, Review } from "@/types/api";

const CATEGORIES: [key: keyof ListingDetail["rating_breakdown"], label: string][] = [
  ["cleanliness", "Cleanliness"],
  ["accuracy", "Accuracy"],
  ["check_in", "Check-in"],
  ["communication", "Communication"],
  ["location", "Location"],
  ["value", "Value"],
];

const month = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" });

function ReviewItem({ review }: { review: Review }) {
  return (
    <li>
      <div className="mb-3 flex items-center gap-3">
        <Avatar firstName={review.author_first_name} lastName={review.author_last_initial} url={review.author_avatar_url} size={48} />
        <div>
          <p className="font-semibold">{review.author_first_name}</p>
          <p className="text-sm text-muted">{month.format(new Date(review.created_at))}</p>
        </div>
      </div>
      <p className="whitespace-pre-line">{review.comment}</p>
    </li>
  );
}

/** Rating summary (overall, per-category bars, star distribution) and the written reviews, paged. */
export function ReviewsSection({ listing }: { listing: ListingDetail }) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [all, setAll] = useState(false);
  const [loading, setLoading] = useState(false);

  const load = (next: number) => {
    setLoading(true);
    listingsApi
      .reviews(listing.id, next, 6)
      .then((result) => {
        setReviews((r) => (next === 1 ? result.items : [...r, ...result.items]));
        setTotal(result.total);
        setPage(next);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let current = true;
    listingsApi
      .reviews(listing.id, 1, 6)
      .then((result) => {
        if (!current) return;
        setReviews(result.items);
        setTotal(result.total);
        setPage(1);
      })
      .catch(() => undefined);
    return () => {
      current = false;
    };
  }, [listing.id]);

  if (listing.rating_avg === null || listing.review_count === 0) {
    return (
      <section id="reviews" className="border-t border-line-soft py-10">
        <h2 className="flex items-center gap-2 text-[22px] font-semibold">
          <Star size={20} className="fill-ink" /> New
        </h2>
        <p className="mt-2 text-muted">No reviews yet.</p>
      </section>
    );
  }

  const distribution = [5, 4, 3, 2, 1].map((stars) => [stars, listing.rating_distribution[String(stars)] ?? 0] as const);
  const biggest = Math.max(1, ...distribution.map(([, n]) => n));

  return (
    <section id="reviews" className="border-t border-line-soft py-10">
      <h2 className="mb-8 flex items-center gap-2 text-[22px] font-semibold">
        <Star size={20} className="fill-ink" /> {listing.rating_avg.toFixed(2)} · {listing.review_count} review{listing.review_count === 1 ? "" : "s"}
      </h2>

      <div className="mb-10 grid gap-8 md:grid-cols-[200px_1fr]">
        <ul className="space-y-1.5" aria-label="Rating distribution">
          {distribution.map(([stars, n]) => (
            <li key={stars} className="flex items-center gap-2 text-xs">
              <span className="w-2">{stars}</span>
              <span className="h-1 flex-1 rounded bg-line-soft">
                <span className="block h-1 rounded bg-ink" style={{ width: `${(n / biggest) * 100}%` }} />
              </span>
            </li>
          ))}
        </ul>
        <ul className="grid grid-cols-2 gap-x-10 gap-y-4 md:grid-cols-3">
          {CATEGORIES.map(([key, label]) => (
            <li key={key} className="border-r border-line-soft pr-4 last:border-0">
              <p className="text-sm font-medium">{label}</p>
              <p className="text-lg font-semibold">{listing.rating_breakdown[key]?.toFixed(1) ?? "–"}</p>
            </li>
          ))}
        </ul>
      </div>

      <ul className="grid gap-x-20 gap-y-10 md:grid-cols-2">
        {reviews.slice(0, 6).map((review) => (
          <ReviewItem key={review.id} review={review} />
        ))}
      </ul>
      {total > 6 && (
        <Button variant="secondary" size="lg" className="mt-10" onClick={() => setAll(true)}>
          Show all {total} reviews
        </Button>
      )}

      <Modal open={all} onClose={() => setAll(false)} title={`${listing.rating_avg.toFixed(2)} · ${total} reviews`} className="md:!max-w-[680px]">
        <ul className="space-y-8 p-6">
          {reviews.map((review) => (
            <ReviewItem key={review.id} review={review} />
          ))}
        </ul>
        {reviews.length < total && (
          <div className="px-6 pb-6">
            <Button variant="secondary" loading={loading} onClick={() => load(page + 1)}>
              Load more
            </Button>
          </div>
        )}
      </Modal>
    </section>
  );
}
