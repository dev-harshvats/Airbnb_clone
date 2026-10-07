"use client";

import { Grid3x3 } from "lucide-react";
import { useState } from "react";

import { Modal } from "@/components/ui/Modal";
import type { PhotoRef } from "@/types/api";

/**
 * Detail-page gallery: one large photo and four smaller ones, with a "Show all photos" button that
 * opens every photo in a scrolling viewer (phones get a swipeable strip instead).
 */
export function PhotoGrid({ photos, title }: { photos: PhotoRef[]; title: string }) {
  const [open, setOpen] = useState(false);
  if (photos.length === 0) return <div className="aspect-[2/1] rounded-card bg-surface" />;

  const tile = (photo: PhotoRef, className: string) => (
    <button key={photo.url} onClick={() => setOpen(true)} className={`group relative overflow-hidden bg-surface ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element -- already resized WebP renditions */}
      <img src={photo.card_url} alt={title} className="size-full object-cover transition duration-300 group-hover:brightness-90" />
    </button>
  );

  return (
    <>
      {/* phones: a swipeable strip */}
      <div className="no-scrollbar -mx-4 flex snap-x overflow-x-auto md:hidden">
        {photos.map((photo) => (
          // eslint-disable-next-line @next/next/no-img-element -- already resized WebP renditions
          <img key={photo.url} src={photo.url} alt={title} className="aspect-[4/3] w-full shrink-0 snap-center object-cover" />
        ))}
      </div>

      {/* tablet and desktop: 1 + 4 */}
      <div className="relative hidden aspect-[2/1] max-h-[420px] grid-cols-4 grid-rows-2 gap-2 overflow-hidden rounded-card md:grid">
        {tile(photos[0], "col-span-2 row-span-2")}
        {photos.slice(1, 5).map((photo) => tile(photo, ""))}
        <button
          onClick={() => setOpen(true)}
          className="absolute bottom-4 right-4 flex items-center gap-2 rounded-control border border-ink bg-white px-4 py-1.5 text-sm font-semibold hover:bg-surface"
        >
          <Grid3x3 size={14} /> Show all photos
        </button>
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Photo tour" className="md:max-w-[900px]">
        <div className="space-y-2 p-4">
          {photos.map((photo) => (
            // eslint-disable-next-line @next/next/no-img-element -- full-size renditions
            <img key={photo.url} src={photo.url} alt={title} className="w-full rounded-control" />
          ))}
        </div>
      </Modal>
    </>
  );
}
