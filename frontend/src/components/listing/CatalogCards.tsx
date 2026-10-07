"use client";

import { Heart, Star } from "lucide-react";
import Link from "next/link";
import type { MouseEvent } from "react";

import { toast } from "@/components/ui/Toast";
import { formatDuration, formatINR, formatTime } from "@/lib/format";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";
import type { ExperienceCard as Experience, PhotoRef, ServiceCard as Service } from "@/types/api";

/**
 * Experiences and services are browse-only for now, so their hearts ask visitors to log in and
 * tell members that saving them is not available yet (stays can be saved).
 */
function SoonHeart() {
  const status = useAuth((s) => s.status);
  const openAuth = useUi((s) => s.openAuth);
  const onClick = (event: MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (status !== "authed") openAuth();
    else toast.error("Saving experiences and services is coming soon");
  };
  return (
    <button onClick={onClick} aria-label="Save" className="absolute right-3 top-3 grid size-8 place-items-center active:scale-90">
      <Heart size={24} strokeWidth={2} className="fill-black/50 stroke-white" />
    </button>
  );
}

function Rating({ avg, count }: { avg: number | null; count: number }) {
  if (avg === null) return <span>★ New</span>;
  return (
    <span className="flex items-center gap-1">
      <Star size={12} className="fill-ink" />
      {avg.toFixed(count > 0 ? 2 : 1)}
    </span>
  );
}

function Photo({ photos, alt, badge }: { photos: PhotoRef[]; alt: string; badge?: string }) {
  return (
    <div className="relative aspect-square overflow-hidden rounded-[14px] bg-surface">
      {photos[0] && (
        // eslint-disable-next-line @next/next/no-img-element -- already resized WebP renditions
        <img src={photos[0].card_url} alt={alt} loading="lazy" className="size-full object-cover" />
      )}
      {badge && (
        <span className="absolute left-3 top-3 rounded-full bg-white px-2.5 py-1 text-[13px] font-semibold shadow-pill">
          {badge}
        </span>
      )}
      <SoonHeart />
    </div>
  );
}

/** An experience: start-time pill on the photo, then title and "From ₹X / guest · ★ rating". */
export function ExperienceCard({ experience }: { experience: Experience }) {
  return (
    <Link href={`/experiences/${experience.id}`} className="block">
      <Photo photos={experience.photos} alt={experience.title} badge={formatTime(experience.start_time)} />
      <div className="mt-2.5 text-sm leading-snug">
        <h3 className="line-clamp-2 font-semibold">{experience.title}</h3>
        <p className="flex items-center gap-1 text-muted">
          <span>
            From {formatINR(experience.price_per_guest)} / guest · {formatDuration(experience.duration_minutes)}
          </span>
          <span aria-hidden>·</span>
          <Rating avg={experience.rating_avg} count={experience.review_count} />
        </p>
      </div>
    </Link>
  );
}

const UNIT: Record<string, string> = { guest: "guest", hour: "hour", session: "session" };

/** A service: "Popular" badge, then title and "From ₹X / session · ★ rating". */
export function ServiceCard({ service }: { service: Service }) {
  return (
    <Link href={`/services/${service.id}`} className="block">
      <Photo photos={service.photos} alt={service.title} badge={service.is_popular ? "Popular" : undefined} />
      <div className="mt-2.5 text-sm leading-snug">
        <h3 className="line-clamp-2 font-semibold">{service.title}</h3>
        <p className="flex items-center gap-1 text-muted">
          <span>
            From {formatINR(service.price_from)} / {UNIT[service.price_unit] ?? service.price_unit}
          </span>
          <span aria-hidden>·</span>
          <Rating avg={service.rating_avg} count={service.review_count} />
        </p>
      </div>
    </Link>
  );
}
