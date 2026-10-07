import { api } from "@/lib/api/client";
import type { Booking, PaymentMethod, TripScope } from "@/types/api";

export type BookingRequest = {
  listing_id: number;
  check_in: string;
  check_out: string;
  adults: number;
  children: number;
  infants: number;
  pets: number;
  payment_method: PaymentMethod;
};

export type ReviewInput = {
  cleanliness: number;
  accuracy: number;
  check_in: number;
  communication: number;
  location: number;
  value: number;
  comment: string;
};

export const bookingsApi = {
  // A retry with the same key returns the original booking instead of making a second one.
  create: (body: BookingRequest, idempotencyKey: string) =>
    api<Booking>("/bookings", { method: "POST", body, headers: { "Idempotency-Key": idempotencyKey } }),
  list: (scope: TripScope) => api<Booking[]>("/bookings", { query: { scope } }),
  get: (code: string) => api<Booking>(`/bookings/${code}`),
  cancel: (code: string) => api<Booking>(`/bookings/${code}/cancel`, { method: "POST" }),
  review: (code: string, body: ReviewInput) => api<{ status: string }>(`/bookings/${code}/review`, { method: "POST", body }),
};
