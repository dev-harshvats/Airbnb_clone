import { api } from "@/lib/api/client";

export type Wishlist = { id: number; name: string; item_count: number; cover_url: string | null };

export const wishlistsApi = {
  list: () => api<Wishlist[]>("/wishlists"),
  create: (name: string) => api<Wishlist>("/wishlists", { method: "POST", body: { name } }),
  savedIds: () => api<{ listing_ids: number[] }>("/wishlists/saved-ids").then((r) => r.listing_ids),
  add: (wishlistId: number, listingId: number) =>
    api<void>(`/wishlists/${wishlistId}/items/${listingId}`, { method: "PUT" }),
  remove: (wishlistId: number, listingId: number) =>
    api<void>(`/wishlists/${wishlistId}/items/${listingId}`, { method: "DELETE" }),
};
