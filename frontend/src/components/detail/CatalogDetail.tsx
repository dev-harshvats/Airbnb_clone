"use client";

import { Heart, MapPin, Share, Star } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { PhotoGrid } from "@/components/listing/PhotoGrid";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { catalogApi } from "@/lib/api/catalog";
import { formatDuration, formatINR, formatTime } from "@/lib/format";
import { searchPath } from "@/lib/routes";
import type { ExperienceDetail, HostProfile, PhotoItem, ServiceDetail } from "@/types/api";

type Loaded<T> = { status: "loading" } | { status: "missing" } | { status: "ready"; data: T };

function useDetail<T>(load: () => Promise<T>, deps: unknown[]): Loaded<T> {
  const [state, setState] = useState<{ deps: string; value: Loaded<T> }>({ deps: "", value: { status: "loading" } });
  const key = JSON.stringify(deps);
  useEffect(() => {
    let current = true;
    load()
      .then((data) => current && setState({ deps: key, value: { status: "ready", data } }))
      .catch(() => current && setState({ deps: key, value: { status: "missing" } }));
    return () => {
      current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only when the id changes
  }, [key]);
  return state.deps === key ? state.value : { status: "loading" };
}

function Skeletons() {
  return (
    <main className="mx-auto max-w-[1120px] space-y-4 px-4 py-8 md:px-6">
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="aspect-[2/1] max-h-[420px] w-full rounded-card" />
    </main>
  );
}

function Missing({ noun, backTo }: { noun: string; backTo: string }) {
  return (
    <main className="mx-auto flex max-w-[560px] flex-col items-center gap-4 px-6 py-24 text-center">
      <h1 className="text-[28px] font-bold">That {noun} isn&apos;t available</h1>
      <p className="text-muted">It may have been removed. Browse other {noun}s instead.</p>
      <Link href={backTo}>
        <Button size="lg">Keep exploring</Button>
      </Link>
    </main>
  );
}

function TitleRow({ title }: { title: string }) {
  const share = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard");
    } catch {
      toast.error("Could not copy the link");
    }
  };
  return (
    <div className="flex items-start justify-between gap-4">
      <h1 className="text-[26px] font-semibold leading-tight">{title}</h1>
      <div className="flex shrink-0 gap-1 text-sm font-medium">
        <button onClick={share} className="flex items-center gap-2 rounded-control px-3 py-2 underline hover:bg-surface">
          <Share size={16} /> Share
        </button>
        <button
          onClick={() => toast.error("Saving experiences and services is coming soon")}
          className="flex items-center gap-2 rounded-control px-3 py-2 underline hover:bg-surface"
        >
          <Heart size={16} /> Save
        </button>
      </div>
    </div>
  );
}

function Rating({ avg, count }: { avg: number | null; count: number }) {
  return avg === null ? (
    <span>★ New</span>
  ) : (
    <span className="flex items-center gap-1">
      <Star size={14} className="fill-ink" /> {avg.toFixed(2)} · <span className="underline">{count} reviews</span>
    </span>
  );
}

function HostRow({ host, label }: { host: HostProfile; label: string }) {
  return (
    <div className="flex items-center gap-4 border-b border-line-soft py-6">
      <Avatar firstName={host.first_name} lastName={host.last_initial} url={host.avatar_url} size={48} />
      <div>
        <p className="font-semibold">
          {label} {host.first_name}
        </p>
        <p className="text-sm text-muted">{host.is_superhost ? "Superhost" : "Host"} · Joined in {new Date(host.joined_at).getFullYear()}</p>
      </div>
    </div>
  );
}

function ReserveCard({ price, unit, onReserve }: { price: string; unit: string; onReserve: () => void }) {
  return (
    <aside className="rounded-[12px] border border-line p-6 shadow-card lg:sticky lg:top-28 lg:lg:self-start">
      <p>
        <span className="text-[22px] font-semibold">From {price}</span> <span className="text-muted">/ {unit}</span>
      </p>
      <Button size="lg" fullWidth className="mt-4" onClick={onReserve}>
        Check availability
      </Button>
      <p className="mt-3 text-center text-sm text-muted">You won&apos;t be charged yet</p>
    </aside>
  );
}

function Details({ photos, title, header, body, card }: { photos: PhotoItem[]; title: string; header: ReactNode; body: ReactNode; card: ReactNode }) {
  return (
    <main className="mx-auto max-w-[1120px] px-4 py-6 md:px-6">
      <TitleRow title={title} />
      <div className="mt-6">
        <PhotoGrid photos={photos} title={title} />
      </div>
      <div className="mt-8 grid gap-12 lg:grid-cols-[1fr_380px]">
        <div>
          {header}
          {body}
        </div>
        {card}
      </div>
    </main>
  );
}

const comingSoon = () => toast.error("Reservations are coming soon");

export function ExperienceDetailView({ id }: { id: string }) {
  const loaded = useDetail<ExperienceDetail>(() => catalogApi.experience(id), [id]);
  if (loaded.status === "loading") return <Skeletons />;
  if (loaded.status === "missing") return <Missing noun="experience" backTo="/experiences" />;
  const e = loaded.data;
  return (
    <Details
      photos={e.all_photos}
      title={e.title}
      header={
        <div className="border-b border-line-soft pb-6">
          <p className="flex items-center gap-1 text-[15px] font-medium">
            <MapPin size={16} /> {e.city}, {e.state}
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
            <Rating avg={e.rating_avg} count={e.review_count} />
            <span>· Starts {formatTime(e.start_time)}</span>
            <span>· {formatDuration(e.duration_minutes)}</span>
            <span>· Up to {e.max_guests} guests</span>
          </p>
          <HostRow host={e.host} label="Hosted by" />
        </div>
      }
      body={
        <section className="py-6">
          <h2 className="mb-3 text-[22px] font-semibold">About this experience</h2>
          <p className="whitespace-pre-line leading-relaxed">{e.description}</p>
          <Link href={searchPath("experiences", e.city)} className="mt-6 inline-block font-semibold underline">
            More experiences in {e.city}
          </Link>
        </section>
      }
      card={<ReserveCard price={formatINR(e.price_per_guest)} unit="guest" onReserve={comingSoon} />}
    />
  );
}

export function ServiceDetailView({ id }: { id: string }) {
  const loaded = useDetail<ServiceDetail>(() => catalogApi.service(id), [id]);
  if (loaded.status === "loading") return <Skeletons />;
  if (loaded.status === "missing") return <Missing noun="service" backTo="/services" />;
  const s = loaded.data;
  return (
    <Details
      photos={s.all_photos}
      title={s.title}
      header={
        <div className="border-b border-line-soft pb-6">
          <p className="flex items-center gap-1 text-[15px] font-medium">
            <MapPin size={16} /> {s.city}, {s.state}
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
            <Rating avg={s.rating_avg} count={s.review_count} />
            {s.is_popular && <span>· Popular</span>}
          </p>
          <HostRow host={s.host} label="Provided by" />
        </div>
      }
      body={
        <section className="py-6">
          <h2 className="mb-3 text-[22px] font-semibold">About this service</h2>
          <p className="whitespace-pre-line leading-relaxed">{s.description}</p>
          <Link href={searchPath("services", s.city, { service_type: s.service_type })} className="mt-6 inline-block font-semibold underline">
            More services in {s.city}
          </Link>
        </section>
      }
      card={<ReserveCard price={formatINR(s.price_from)} unit={s.price_unit} onReserve={comingSoon} />}
    />
  );
}

