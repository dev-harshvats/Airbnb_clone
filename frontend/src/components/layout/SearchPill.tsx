"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Modal } from "@/components/ui/Modal";
import { searchPath } from "@/lib/routes";

/** Phone version: a full-width pill that opens the search in a sheet. */
export function MobileSearchPill() {
  const [open, setOpen] = useState(false);
  const [where, setWhere] = useState("");
  const router = useRouter();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setOpen(false);
    router.push(searchPath("homes", where.trim() || null));
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Start your search"
        className="flex w-full items-center gap-3 rounded-full border border-line bg-white px-4 py-2.5 text-left shadow-pill"
      >
        <Search size={18} strokeWidth={2.5} />
        <span className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">Where to?</span>
          <span className="text-xs text-muted">Anywhere · Any week · Add guests</span>
        </span>
      </button>
      <Modal open={open} onClose={() => setOpen(false)} title="Search">
        <form onSubmit={submit} className="space-y-4 p-6">
          <label className="block rounded-card border border-line p-4">
            <span className="text-xs font-bold">Where</span>
            <input
              autoFocus
              value={where}
              onChange={(e) => setWhere(e.target.value)}
              placeholder="Search destinations"
              className="mt-1 w-full bg-transparent text-base outline-none"
            />
          </label>
          <button type="submit" className="w-full rounded-control bg-rausch-gradient py-3 font-semibold text-white">
            Search
          </button>
        </form>
      </Modal>
    </>
  );
}
