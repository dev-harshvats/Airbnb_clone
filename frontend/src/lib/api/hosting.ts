import { api } from "@/lib/api/client";
import type { Category, HostListing, HostStats, ListingDetail, PhotoItem, Reservation, User } from "@/types/api";

type ListingBody = Record<string, unknown>;

export const hostingApi = {
  becomeHost: () => api<User>("/users/me/become-host", { method: "POST" }),
  categories: () => api<Category[]>("/categories"),
  listings: () => api<HostListing[]>("/hosting/listings"),
  createListing: (body: ListingBody) => api<ListingDetail>("/hosting/listings", { method: "POST", body }),
  updateListing: (id: number, body: ListingBody) => api<ListingDetail>(`/hosting/listings/${id}`, { method: "PATCH", body }),
  deleteListing: (id: number) => api<void>(`/hosting/listings/${id}`, { method: "DELETE" }),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api<PhotoItem>(`/hosting/listings/${id}/photos`, { method: "POST", body: form });
  },
  reorderPhotos: (id: number, photoIds: number[]) =>
    api<PhotoItem[]>(`/hosting/listings/${id}/photos/order`, { method: "PUT", body: { photo_ids: photoIds } }),
  deletePhoto: (id: number, photoId: number) => api<void>(`/hosting/listings/${id}/photos/${photoId}`, { method: "DELETE" }),
  reservations: (status?: "upcoming" | "past" | "cancelled") => api<Reservation[]>("/hosting/reservations", { query: { status } }),
  stats: () => api<HostStats>("/hosting/stats"),
};
