import { api } from "@/lib/api/client";
import type { ListingCard } from "@/types/api";

export type Wishlist = { id: number; name: string; item_count: number; cover_url: string | null };
export type WishlistDetail = { id: number; name: string; listings: ListingCard[] };

export const wishlistsApi = {
  list: () => api<Wishlist[]>("/wishlists"),
  detail: (id: number | string) => api<WishlistDetail>(`/wishlists/${id}`),
  create: (name: string) => api<Wishlist>("/wishlists", { method: "POST", body: { name } }),
  delete: (id: number) => api<void>(`/wishlists/${id}`, { method: "DELETE" }),
  savedIds: () => api<{ listing_ids: number[] }>("/wishlists/saved-ids").then((r) => r.listing_ids),
  add: (wishlistId: number, listingId: number) =>
    api<void>(`/wishlists/${wishlistId}/items/${listingId}`, { method: "PUT" }),
  remove: (wishlistId: number, listingId: number) =>
    api<void>(`/wishlists/${wishlistId}/items/${listingId}`, { method: "DELETE" }),
};
