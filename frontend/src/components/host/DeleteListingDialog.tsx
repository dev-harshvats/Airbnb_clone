"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ApiError } from "@/lib/api/client";
import { hostingApi } from "@/lib/api/hosting";

type Props = {
  listing: { id: number; title: string; status: "draft" | "active" | "inactive" };
  onClose: () => void;
  onDeleted: () => void;
  /** Offered when the server refuses because the listing already has bookings. */
  onUnlist?: () => void;
};

/**
 * Type-the-title-to-confirm delete. A listing that has ever been booked can't be deleted (guests'
 * trips must stay readable); the server says so with a 409 and this dialog offers to unlist instead.
 * Mount it only while open.
 */
export function DeleteListingDialog({ listing, onClose, onDeleted, onUnlist }: Props) {
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const remove = async () => {
    setBusy(true);
    setError(null);
    try {
      await hostingApi.deleteListing(listing.id);
      onDeleted();
    } catch (err) {
      setBusy(false);
      setError(err instanceof ApiError ? err.detail : "We couldn't delete this listing.");
    }
  };

  return (
    <Modal open onClose={onClose} title="Delete this listing?" className="md:!max-w-[480px]">
      <div className="p-6">
        <p>
          This permanently deletes <strong>{listing.title}</strong> and its photos. To confirm, type the title below.
        </p>
        <input
          aria-label="Type the listing title to confirm"
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="mt-4 w-full rounded-control border border-muted px-3 py-3 focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
        />
        {error && (
          <div role="alert" className="mt-4 rounded-control bg-[#fff0ef] p-3 text-sm text-[#c13515]">
            {error}
            {onUnlist && listing.status === "active" && (
              <button onClick={onUnlist} className="mt-2 block font-semibold underline">
                Unlist it instead
              </button>
            )}
          </div>
        )}
        <div className="mt-6 flex justify-between">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="dark" loading={busy} disabled={text.trim() !== listing.title} onClick={remove}>
            Delete listing
          </Button>
        </div>
      </div>
    </Modal>
  );
}
