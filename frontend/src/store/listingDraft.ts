import { create } from "zustand";
import { persist } from "zustand/middleware";

import { emptyDraft, type ListingDraft } from "@/lib/hosting";

type DraftState = {
  /** Whose draft this is, so a different account logging in on this browser starts fresh. */
  ownerId: number | null;
  /** Set once the draft has been saved to the server (from the photos step on). */
  listingId: number | null;
  draft: ListingDraft;
  patch: (changes: Partial<ListingDraft>) => void;
  setListingId: (id: number | null) => void;
  claim: (ownerId: number) => void;
  reset: () => void;
};

/** The wizard's in-progress answers. Kept in localStorage so a reload doesn't lose them. */
export const useListingDraft = create<DraftState>()(
  persist(
    (set, get) => ({
      ownerId: null,
      listingId: null,
      draft: emptyDraft(),
      patch: (changes) => set({ draft: { ...get().draft, ...changes } }),
      setListingId: (listingId) => set({ listingId }),
      claim: (ownerId) => {
        if (get().ownerId !== ownerId) set({ ownerId, listingId: null, draft: emptyDraft() });
      },
      reset: () => set({ listingId: null, draft: emptyDraft() }),
    }),
    { name: "airbnb:listing-draft" },
  ),
);
