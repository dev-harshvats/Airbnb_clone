"use client";

import { Heart } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/Skeleton";
import { wishlistsApi, type Wishlist } from "@/lib/api/wishlists";

/** /wishlists: one tile per wishlist, with its cover photo, name and how many stays are in it. */
export function WishlistsPage() {
  const [lists, setLists] = useState<Wishlist[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let current = true;
    wishlistsApi
      .list()
      .then((result) => current && setLists(result))
      .catch(() => current && setFailed(true));
    return () => {
      current = false;
    };
  }, []);

  return (
    <main className="mx-auto max-w-[1280px] px-6 py-10 xl:px-20">
      <h1 className="mb-8 text-[32px] font-semibold">Wishlists</h1>

      {failed && <p className="text-muted">We couldn&apos;t load your wishlists. Please try again.</p>}
      {lists === null && !failed && (
        <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="aspect-square w-full rounded-[20px]" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ))}
        </div>
      )}
      {lists?.length === 0 && (
        <div className="py-12">
          <h2 className="text-xl font-semibold">Create your first wishlist</h2>
          <p className="mt-1 text-muted">As you search, tap the heart icon to save your favourite places to a wishlist.</p>
          <Link href="/" className="mt-6 inline-block rounded-control bg-ink px-6 py-3 font-semibold text-white">
            Start exploring
          </Link>
        </div>
      )}
      {lists && lists.length > 0 && (
        <ul className="grid grid-cols-2 gap-x-6 gap-y-8 md:grid-cols-3 lg:grid-cols-4">
          {lists.map((wishlist) => (
            <li key={wishlist.id}>
              <Link href={`/wishlists/${wishlist.id}`} className="group block">
                <span className="mb-3 grid aspect-square place-items-center overflow-hidden rounded-[20px] bg-surface shadow-pill">
                  {wishlist.cover_url ? (
                    // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
                    <img src={wishlist.cover_url} alt="" className="size-full object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
                  ) : (
                    <Heart size={36} className="text-muted" />
                  )}
                </span>
                <span className="block truncate font-semibold">{wishlist.name}</span>
                <span className="text-sm text-muted">{wishlist.item_count} saved</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
