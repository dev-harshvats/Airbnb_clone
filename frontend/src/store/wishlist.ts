import { create } from "zustand";

import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { wishlistsApi } from "@/lib/api/wishlists";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

const DEFAULT_NAME = "Saved stays";

type WishlistState = {
  savedIds: Set<number>;
  /** listing id -> the wishlist it was saved to during this visit (so it can be un-saved). */
  savedTo: Map<number, number>;
  load: () => Promise<void>;
  clear: () => void;
  toggle: (listingId: number) => Promise<void>;
};

export const useWishlist = create<WishlistState>((set, get) => ({
  savedIds: new Set(),
  savedTo: new Map(),

  async load() {
    try {
      set({ savedIds: new Set(await wishlistsApi.savedIds()) });
    } catch {
      /* hearts simply start empty if this fails */
    }
  },

  clear: () => set({ savedIds: new Set(), savedTo: new Map() }),

  async toggle(listingId) {
    if (useAuth.getState().status !== "authed") return useUi.getState().openAuth();

    const { savedIds, savedTo } = get();
    const wasSaved = savedIds.has(listingId);
    const apply = (saved: boolean) => {
      const next = new Set(get().savedIds);
      if (saved) next.add(listingId);
      else next.delete(listingId);
      set({ savedIds: next });
    };

    apply(!wasSaved); // optimistic: the heart flips immediately
    try {
      if (wasSaved) {
        const wishlistId = savedTo.get(listingId) ?? (await findDefaultWishlist())?.id;
        if (wishlistId) await wishlistsApi.remove(wishlistId, listingId);
        toast.success("Removed from wishlist");
      } else {
        const wishlist = (await findDefaultWishlist()) ?? (await wishlistsApi.create(DEFAULT_NAME));
        await wishlistsApi.add(wishlist.id, listingId);
        set({ savedTo: new Map(get().savedTo).set(listingId, wishlist.id) });
        toast.success(`Saved to ${wishlist.name}`);
      }
    } catch (error) {
      apply(wasSaved); // roll back
      toast.error(error instanceof ApiError ? error.detail : "Could not update your wishlist.");
    }
  },
}));

async function findDefaultWishlist() {
  return (await wishlistsApi.list()).find((w) => w.name === DEFAULT_NAME);
}
