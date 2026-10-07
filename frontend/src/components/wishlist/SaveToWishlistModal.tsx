"use client";

import { Heart, Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { wishlistsApi, type Wishlist } from "@/lib/api/wishlists";
import { useUi } from "@/store/ui";
import { useWishlist } from "@/store/wishlist";

/** Where does the stay go? Pick one of your wishlists or start a new one. Mounted once in Providers. */
export function SaveToWishlistModal() {
  const listingId = useUi((s) => s.saveListingId);
  const close = useUi((s) => s.closeSave);
  // Mount the body only while open, so each opening starts fresh and reloads the wishlists.
  return listingId === null ? null : <Body listingId={listingId} onClose={close} />;
}

function Body({ listingId, onClose }: { listingId: number; onClose: () => void }) {
  const save = useWishlist((s) => s.save);
  const [lists, setLists] = useState<Wishlist[] | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let current = true;
    wishlistsApi
      .list()
      .then((result) => {
        if (!current) return;
        setLists(result);
        setCreating(result.length === 0);
      })
      .catch(() => current && setLists([]));
    return () => {
      current = false;
    };
  }, []);

  const saveTo = async (wishlist: Wishlist) => {
    setBusy(true);
    try {
      await save(listingId, wishlist);
      onClose();
    } catch {
      setBusy(false);
    }
  };

  const create = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    let wishlist: Wishlist;
    try {
      wishlist = await wishlistsApi.create(name.trim());
    } catch (error) {
      setBusy(false);
      toast.error(error instanceof ApiError ? error.detail : "Could not create the wishlist.");
      return;
    }
    await saveTo(wishlist);
  };

  return (
    <Modal open onClose={onClose} title="Save to wishlist" className="md:!max-w-[480px]">
      <div className="p-6">
        {lists === null && <p className="py-8 text-center text-muted">Loading your wishlists…</p>}

        {lists !== null && lists.length > 0 && !creating && (
          <>
            <ul className="grid grid-cols-2 gap-4">
              {lists.map((wishlist) => (
                <li key={wishlist.id}>
                  <button type="button" disabled={busy} onClick={() => saveTo(wishlist)} className="block w-full text-left disabled:opacity-60">
                    <span className="mb-2 grid aspect-square place-items-center overflow-hidden rounded-[12px] bg-surface">
                      {wishlist.cover_url ? (
                        // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
                        <img src={wishlist.cover_url} alt="" className="size-full object-cover" />
                      ) : (
                        <Heart size={28} className="text-muted" />
                      )}
                    </span>
                    <span className="block truncate text-sm font-semibold">{wishlist.name}</span>
                    <span className="text-sm text-muted">{wishlist.item_count} saved</span>
                  </button>
                </li>
              ))}
            </ul>
            <Button variant="secondary" fullWidth className="mt-6" onClick={() => setCreating(true)}>
              <Plus size={16} /> Create new wishlist
            </Button>
          </>
        )}

        {lists !== null && creating && (
          <form onSubmit={create}>
            <label className="block">
              <span className="mb-2 block text-base font-semibold">Name</span>
              <input
                autoFocus
                maxLength={50}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Goa weekend"
                className="w-full rounded-control border border-muted px-3 py-3 text-base focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
              />
              <span className="mt-1 block text-right text-xs text-muted">{name.length}/50 characters</span>
            </label>
            <div className="mt-6 flex items-center justify-between">
              {lists.length > 0 ? (
                <button type="button" onClick={() => setCreating(false)} className="font-semibold underline">
                  Back
                </button>
              ) : (
                <span />
              )}
              <Button type="submit" variant="dark" size="lg" disabled={!name.trim()} loading={busy}>
                Create
              </Button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
}
