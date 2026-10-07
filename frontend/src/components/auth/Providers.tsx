"use client";

import { useEffect } from "react";

import { AuthModal } from "@/components/auth/AuthModal";
import { Toaster } from "@/components/ui/Toast";
import { useAuth } from "@/store/auth";
import { useWishlist } from "@/store/wishlist";

/** Client-side singletons mounted once in the root layout: session restore, login dialog, toasts. */
export function Providers() {
  const status = useAuth((s) => s.status);

  useEffect(() => {
    void useAuth.getState().bootstrap();
  }, []);

  // Hearts reflect the logged-in user's saved stays, and reset when they log out.
  useEffect(() => {
    if (status === "authed") void useWishlist.getState().load();
    if (status === "anon") useWishlist.getState().clear();
  }, [status]);
  return (
    <>
      <AuthModal />
      <Toaster />
    </>
  );
}
