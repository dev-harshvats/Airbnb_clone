"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DeleteListingDialog } from "@/components/host/DeleteListingDialog";
import { STEP_TITLES, StepBody } from "@/components/host/StepBody";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { hostingApi } from "@/lib/api/hosting";
import { listingsApi } from "@/lib/api/listings";
import { draftFromListing, toPayload, validateStep, type ListingDraft, type StepKey } from "@/lib/hosting";
import type { Category, ListingDetail, PhotoItem } from "@/types/api";

const SECTIONS: { key: string; label: string; steps: StepKey[] }[] = [
  { key: "photos", label: "Photos", steps: ["photos"] },
  { key: "title", label: "Title", steps: ["title"] },
  { key: "description", label: "Description", steps: ["description"] },
  { key: "basics", label: "Property and rooms", steps: ["property-type", "place-type", "floor-plan", "category"] },
  { key: "pricing", label: "Pricing", steps: ["price"] },
  { key: "amenities", label: "Amenities", steps: ["amenities"] },
  { key: "location", label: "Location", steps: ["location"] },
  { key: "rules", label: "Rules", steps: ["rules"] },
];

const STATUS: Record<ListingDetail["status"], { label: string; className: string }> = {
  active: { label: "Listed", className: "bg-[#e6f4ea] text-[#0a6b1f]" },
  inactive: { label: "Unlisted", className: "bg-surface text-muted" },
  draft: { label: "In progress", className: "bg-surface text-muted" },
};

/** /hosting/listings/{id}/edit: change one section at a time, publish or unlist, or delete. */
export function ListingEditor({ id }: { id: number }) {
  const router = useRouter();
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [draft, setDraft] = useState<ListingDraft | null>(null);
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [section, setSection] = useState(SECTIONS[0].key);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let current = true;
    listingsApi
      .detail(id)
      .then((result) => {
        if (!current) return;
        setListing(result);
        setDraft(draftFromListing(result));
        setPhotos(result.all_photos);
      })
      .catch(() => current && setMissing(true));
    hostingApi.categories().then(setCategories).catch(() => setCategories([]));
    return () => {
      current = false;
    };
  }, [id]);

  if (missing) {
    return (
      <main className="mx-auto max-w-[560px] px-6 py-24 text-center">
        <h1 className="text-[28px] font-bold">We couldn&apos;t find that listing</h1>
        <Link href="/hosting" className="mt-4 inline-block font-semibold underline">Back to your listings</Link>
      </main>
    );
  }
  if (!listing || !draft) {
    return (
      <main className="mx-auto max-w-[1040px] space-y-4 px-6 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  const current = SECTIONS.find((s) => s.key === section)!;
  const patch = (changes: Partial<ListingDraft>) => setDraft((d) => (d ? { ...d, ...changes } : d));
  const status = STATUS[listing.status];

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setProblem(null);
    try {
      await action();
    } catch (error) {
      setProblem(error instanceof ApiError ? error.detail : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const save = () =>
    run(async () => {
      for (const step of current.steps) {
        const message = validateStep(step, draft, photos.length);
        if (message) throw new ApiError(0, "INVALID", message);
      }
      setListing(await hostingApi.updateListing(id, toPayload(draft, categories[0]?.id)));
      toast.success("Changes saved");
    });

  const setStatus = (next: "active" | "inactive") =>
    run(async () => {
      setListing(await hostingApi.updateListing(id, { status: next }));
      toast.success(next === "active" ? "Your listing is live" : "Your listing is unlisted");
    });

  return (
    <main className="mx-auto max-w-[1040px] px-6 py-8">
      <Link href="/hosting" className="mb-4 inline-flex items-center gap-1 text-sm font-medium hover:underline">
        <ChevronLeft size={16} /> Your listings
      </Link>
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-semibold leading-tight">{listing.title}</h1>
          <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${status.className}`}>{status.label}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {listing.status === "active" && (
            <Link href={`/rooms/${id}`}>
              <Button variant="secondary">View listing</Button>
            </Link>
          )}
          {listing.status === "active" ? (
            <Button variant="secondary" loading={busy} onClick={() => setStatus("inactive")}>Unlist</Button>
          ) : (
            <Button variant="dark" loading={busy} onClick={() => setStatus("active")}>Publish</Button>
          )}
          <Button variant="secondary" onClick={() => setDeleting(true)}>Delete</Button>
        </div>
      </div>

      <div className="grid gap-10 md:grid-cols-[220px_1fr]">
        <nav aria-label="Listing sections" className="flex gap-1 overflow-x-auto md:flex-col">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              onClick={() => { setSection(s.key); setProblem(null); }}
              aria-current={section === s.key ? "true" : undefined}
              className={`whitespace-nowrap rounded-control px-4 py-3 text-left font-medium transition ${section === s.key ? "bg-surface font-semibold" : "hover:bg-surface"}`}
            >
              {s.label}
            </button>
          ))}
        </nav>

        <section>
          <div className="space-y-12">
            {current.steps.map((step) => (
              <div key={step}>
                <h2 className="mb-1 text-2xl font-semibold">{STEP_TITLES[step].title}</h2>
                {STEP_TITLES[step].hint && <p className="mb-6 text-muted">{STEP_TITLES[step].hint}</p>}
                <StepBody step={step} draft={draft} patch={patch} ctx={{ categories, listingId: id, photos, onPhotosChange: setPhotos }} />
              </div>
            ))}
          </div>
          {problem && <p role="alert" className="mt-6 text-sm font-medium text-[#c13515]">{problem}</p>}
          {section !== "photos" && (
            <div className="mt-8">
              <Button variant="dark" size="lg" loading={busy} onClick={save}>Save changes</Button>
            </div>
          )}
        </section>
      </div>

      {deleting && (
        <DeleteListingDialog
          listing={listing}
          onClose={() => setDeleting(false)}
          onDeleted={() => {
            toast.success("Listing deleted");
            router.replace("/hosting");
          }}
          onUnlist={() => {
            setDeleting(false);
            void setStatus("inactive");
          }}
        />
      )}
    </main>
  );
}
