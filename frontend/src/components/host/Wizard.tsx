"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { STEP_TITLES, StepBody, type StepContext } from "@/components/host/StepBody";
import { Button } from "@/components/ui/Button";
import { Logo } from "@/components/ui/Logo";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { hostingApi } from "@/lib/api/hosting";
import { listingsApi } from "@/lib/api/listings";
import { formatINR } from "@/lib/format";
import { WIZARD_STEPS, firstInvalidStep, toPayload, validateStep, type StepKey } from "@/lib/hosting";
import { useAuth } from "@/store/auth";
import { useListingDraft } from "@/store/listingDraft";
import type { Category, PhotoItem } from "@/types/api";

/** Airbnb's three stages, shown as three progress segments. */
const STAGES: StepKey[][] = [
  ["about", "property-type", "place-type", "location", "floor-plan", "amenities"],
  ["photos", "title", "description", "category"],
  ["price", "rules", "review"],
];

/** The draft is first saved to the server when the host reaches the photos step. */
const FIRST_SAVED_STEP = WIZARD_STEPS.indexOf("amenities");

export function Wizard({ step }: { step: StepKey }) {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const updateUser = useAuth((s) => s.updateUser);
  const { draft, listingId, patch, setListingId, claim, reset } = useListingDraft();
  const [categories, setCategories] = useState<Category[]>([]);
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const index = WIZARD_STEPS.indexOf(step);

  useEffect(() => {
    if (user) claim(user.id);
  }, [user, claim]);

  useEffect(() => {
    hostingApi.categories().then(setCategories).catch(() => setCategories([]));
  }, []);

  // Pick up the photos of a draft that was already saved (and forget a draft that no longer exists).
  useEffect(() => {
    if (!listingId) return;
    let current = true;
    listingsApi
      .detail(listingId)
      .then((listing) => current && setPhotos(listing.all_photos))
      .catch(() => current && setListingId(null));
    return () => {
      current = false;
    };
  }, [listingId, setListingId]);

  /** Create the draft on the server, or save the latest answers into it. Returns its id. */
  const save = async (extra: Record<string, unknown> = {}): Promise<number> => {
    const payload = { ...toPayload(draft, categories[0]?.id), ...extra };
    if (listingId) {
      await hostingApi.updateListing(listingId, payload);
      return listingId;
    }
    const created = await hostingApi.createListing(payload);
    setListingId(created.id);
    return created.id;
  };

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  // The photos step needs a saved draft to attach files to (e.g. after a reload with no server draft).
  useEffect(() => {
    if (step === "photos" && !listingId && categories.length > 0) {
      void save().catch(() => setError("We couldn't start your draft. Please go back and try again."));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- start the draft once the categories are in
  }, [step, listingId, categories.length]);

  const go = (target: StepKey) => router.push(`/become-a-host/${target}`);

  const next = () =>
    run(async () => {
      const problem = validateStep(step, draft, photos.length);
      if (problem) throw new ApiError(0, "INVALID", problem);
      if (step === "about" && user && !user.is_host) updateUser(await hostingApi.becomeHost());
      if (listingId || index >= FIRST_SAVED_STEP) await save();
      go(WIZARD_STEPS[index + 1]);
    });

  const publish = () =>
    run(async () => {
      const blocked = firstInvalidStep(draft, photos.length);
      if (blocked) {
        go(blocked);
        throw new ApiError(0, "INVALID", validateStep(blocked, draft, photos.length) ?? "Something is missing.");
      }
      const id = await save({ status: "active" });
      reset();
      toast.success("Your listing is live");
      router.push(`/rooms/${id}`);
    });

  const saveAndExit = () =>
    run(async () => {
      if (listingId || index >= FIRST_SAVED_STEP) await save();
      router.push("/hosting");
    });

  const ctx: StepContext = { categories, listingId, photos, onPhotosChange: setPhotos };
  const meta = STEP_TITLES[step];
  const stage = STAGES.findIndex((s) => s.includes(step));

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex h-20 items-center justify-between px-6 md:px-10">
        <Link href="/" aria-label="Airbnb home">
          <Logo />
        </Link>
        <button onClick={saveAndExit} disabled={busy} className="rounded-full border border-line px-5 py-2.5 text-sm font-semibold hover:border-ink">
          Save &amp; exit
        </button>
      </header>

      <main className="mx-auto w-full max-w-[640px] flex-1 px-6 py-8">
        <h1 className="text-[32px] font-semibold leading-tight">{meta.title}</h1>
        {meta.hint && <p className="mt-2 text-muted">{meta.hint}</p>}
        <div className="mt-8">
          {step === "review" ? <Review draft={draft} photos={photos} categories={categories} /> : <StepBody step={step} draft={draft} patch={patch} ctx={ctx} />}
        </div>
        {error && (
          <p role="alert" className="mt-6 text-sm font-medium text-[#c13515]">
            {error}
          </p>
        )}
      </main>

      <footer className="sticky bottom-0 border-t border-line-soft bg-canvas">
        <div className="flex gap-1.5">
          {STAGES.map((steps, i) => {
            const done = i < stage ? 1 : i === stage ? (steps.indexOf(step) + 1) / steps.length : 0;
            return (
              <div key={i} className="h-1.5 flex-1 bg-line-soft">
                <div className="h-full bg-ink transition-all" style={{ width: `${done * 100}%` }} />
              </div>
            );
          })}
        </div>
        <div className="flex items-center justify-between px-6 py-4 md:px-10">
          {index > 0 ? (
            <button onClick={() => go(WIZARD_STEPS[index - 1])} disabled={busy} className="font-semibold underline">
              Back
            </button>
          ) : (
            <span />
          )}
          {step === "review" ? (
            <Button variant="primary" size="lg" loading={busy} onClick={publish}>
              Publish
            </Button>
          ) : (
            <Button variant="dark" size="lg" loading={busy} onClick={next}>
              {step === "about" ? "Get started" : "Next"}
            </Button>
          )}
        </div>
      </footer>
    </div>
  );
}

function Review({ draft, photos, categories }: { draft: ReturnType<typeof useListingDraft.getState>["draft"]; photos: PhotoItem[]; categories: Category[] }) {
  const problem = firstInvalidStep(draft, photos.length);
  return (
    <div className="overflow-hidden rounded-[16px] border border-line shadow-card">
      {photos[0] && (
        // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
        <img src={photos[0].card_url} alt="" className="aspect-[4/3] w-full object-cover" />
      )}
      <div className="space-y-1 p-5">
        <p className="text-xl font-semibold">{draft.title || "Untitled listing"}</p>
        <p className="text-muted">
          {draft.city ? `${draft.city}, ${draft.state}` : "No location yet"} · {draft.maxGuests} guests · {draft.bedrooms} bedroom{draft.bedrooms === 1 ? "" : "s"}
        </p>
        <p className="text-muted">{categories.find((c) => c.id === draft.categoryId)?.label ?? "No category yet"}</p>
        <p className="pt-2 text-lg">
          <strong>{draft.pricePerNight ? formatINR(draft.pricePerNight) : "—"}</strong> night
        </p>
        {problem && <p className="pt-2 text-sm text-[#c13515]">Not ready yet: {validateStep(problem, draft, photos.length)}</p>}
      </div>
    </div>
  );
}
