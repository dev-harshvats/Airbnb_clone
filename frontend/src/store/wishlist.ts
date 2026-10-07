import { create } from "zustand";

import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { wishlistsApi, type Wishlist } from "@/lib/api/wishlists";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

type WishlistState = {
  /** Every listing saved to any wishlist; drives the filled-in hearts. */
  savedIds: Set<number>;
  load: () => Promise<void>;
  clear: () => void;
  /** Saved -> remove it from the wishlists holding it. Not saved -> open the "Save to wishlist" dialog. */
  toggle: (listingId: number) => Promise<void>;
  /** Put a listing into a wishlist (used by the dialog). Throws on failure after reporting it. */
  save: (listingId: number, wishlist: Wishlist) => Promise<void>;
};

const failure = (error: unknown) => toast.error(error instanceof ApiError ? error.detail : "Could not update your wishlist.");

export const useWishlist = create<WishlistState>((set, get) => {
  const setSaved = (listingId: number, saved: boolean) => {
    const next = new Set(get().savedIds);
    if (saved) next.add(listingId);
    else next.delete(listingId);
    set({ savedIds: next });
  };

  return {
    savedIds: new Set(),

    async load() {
      try {
        set({ savedIds: new Set(await wishlistsApi.savedIds()) });
      } catch {
        /* hearts simply start empty if this fails */
      }
    },

    clear: () => set({ savedIds: new Set() }),

    async toggle(listingId) {
      if (useAuth.getState().status !== "authed") return useUi.getState().openAuth();
      if (!get().savedIds.has(listingId)) return useUi.getState().openSave(listingId);

      setSaved(listingId, false); // optimistic: the heart empties immediately
      try {
        // The saved-ids list doesn't say which wishlist holds a listing, so look through them.
        const lists = await wishlistsApi.list();
        const details = await Promise.all(lists.filter((w) => w.item_count > 0).map((w) => wishlistsApi.detail(w.id)));
        const holding = details.filter((d) => d.listings.some((l) => l.id === listingId));
        await Promise.all(holding.map((d) => wishlistsApi.remove(d.id, listingId)));
        toast.success("Removed from wishlist");
      } catch (error) {
        setSaved(listingId, true);
        failure(error);
      }
    },

    async save(listingId, wishlist) {
      try {
        await wishlistsApi.add(wishlist.id, listingId);
        setSaved(listingId, true);
        toast.success(`Saved to ${wishlist.name}`);
      } catch (error) {
        failure(error);
        throw error;
      }
    },
  };
});
