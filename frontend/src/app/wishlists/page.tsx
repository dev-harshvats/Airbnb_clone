import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { WishlistsPage } from "@/components/wishlist/WishlistsPage";

export const metadata: Metadata = { title: "Wishlists" };

export default function Page() {
  return (
    <RequireAuth>
      <WishlistsPage />
    </RequireAuth>
  );
}
