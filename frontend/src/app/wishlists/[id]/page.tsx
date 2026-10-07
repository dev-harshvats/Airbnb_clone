import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { WishlistDetailPage } from "@/components/wishlist/WishlistDetailPage";

export const metadata: Metadata = { title: "Wishlist" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <RequireAuth>
      <WishlistDetailPage id={id} />
    </RequireAuth>
  );
}
