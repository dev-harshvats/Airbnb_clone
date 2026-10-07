"use client";

import { ChevronLeft, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ListingCard } from "@/components/listing/ListingCard";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { wishlistsApi, type WishlistDetail } from "@/lib/api/wishlists";
import { useWishlist } from "@/store/wishlist";

/** /wishlists/{id}: the saved stays as cards. Un-hearting a card drops it from the page. */
export function WishlistDetailPage({ id }: { id: string }) {
  const router = useRouter();
  const savedIds = useWishlist((s) => s.savedIds);
  const [wishlist, setWishlist] = useState<WishlistDetail | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "missing">("loading");
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let current = true;
    wishlistsApi
      .detail(id)
      .then((result) => {
        if (!current) return;
        setWishlist(result);
        setState("ready");
      })
      .catch(() => current && setState("missing"));
    return () => {
      current = false;
    };
  }, [id]);

  const remove = async () => {
    if (!wishlist) return;
    setDeleting(true);
    try {
      await wishlistsApi.delete(wishlist.id);
      await useWishlist.getState().load(); // hearts for stays that only lived here go back to empty
      toast.success(`Deleted ${wishlist.name}`);
      router.replace("/wishlists");
    } catch (error) {
      setDeleting(false);
      setConfirming(false);
      toast.error(error instanceof ApiError ? error.detail : "Could not delete the wishlist.");
    }
  };

  if (state === "loading") {
    return (
      <div className="mx-auto max-w-[1280px] space-y-6 px-6 py-10 xl:px-20">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (state === "missing" || !wishlist) {
    return (
      <main className="mx-auto max-w-[1280px] px-6 py-16 text-center xl:px-20">
        <h1 className="text-2xl font-semibold">We couldn&apos;t find that wishlist</h1>
        <Link href="/wishlists" className="mt-4 inline-block font-semibold underline">
          Back to wishlists
        </Link>
      </main>
    );
  }

  const listings = wishlist.listings.filter((listing) => savedIds.has(listing.id));
  return (
    <main className="mx-auto max-w-[1280px] px-6 py-10 xl:px-20">
      <Link href="/wishlists" className="mb-4 inline-flex items-center gap-1 text-sm font-medium hover:underline">
        <ChevronLeft size={16} /> Wishlists
      </Link>
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="text-[32px] font-semibold">{wishlist.name}</h1>
        <button
          type="button"
          onClick={() => setConfirming(true)}
          className="flex items-center gap-2 rounded-control border border-line px-4 py-2 text-sm font-medium hover:border-ink"
        >
          <Trash2 size={16} /> Delete
        </button>
      </div>

      {listings.length === 0 ? (
        <p className="text-muted">Nothing saved here yet. Tap the heart on a stay to add it.</p>
      ) : (
        <div className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} variant="grid" />
          ))}
        </div>
      )}

      <Modal open={confirming} onClose={() => setConfirming(false)} title="Delete wishlist?" className="md:!max-w-[420px]">
        <div className="p-6">
          <p className="text-base">
            <strong>{wishlist.name}</strong> and everything saved in it will be removed. This can&apos;t be undone.
          </p>
          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
            <Button variant="dark" loading={deleting} onClick={remove}>
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </main>
  );
}
