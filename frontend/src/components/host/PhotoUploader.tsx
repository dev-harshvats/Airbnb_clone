"use client";

import { ArrowLeft, ArrowRight, ImagePlus, Loader2, Trash2 } from "lucide-react";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { hostingApi } from "@/lib/api/hosting";
import { MIN_PHOTOS } from "@/lib/hosting";
import type { PhotoItem } from "@/types/api";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 5 * 1024 * 1024;

type Props = {
  listingId: number;
  photos: PhotoItem[];
  onChange: (photos: PhotoItem[]) => void;
};

/**
 * Drag files onto the box (or click it) to upload; each file shows its own progress tile. Drag a
 * photo onto another, or use the arrows, to reorder; the first photo is the cover. Every change is
 * saved to the server straight away.
 */
export function PhotoUploader({ listingId, photos, onChange }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState<{ id: number; name: string }[]>([]);
  const [over, setOver] = useState(false);
  const [dragged, setDragged] = useState<number | null>(null);
  // Uploads finish out of step with React renders, so the freshest list is kept here.
  const latest = useRef(photos);
  useEffect(() => {
    latest.current = photos;
  });
  const nextTile = useRef(0);

  const upload = async (files: File[]) => {
    for (const file of files) {
      if (!ACCEPTED.includes(file.type)) {
        toast.error(`${file.name}: only JPEG, PNG and WebP images are allowed.`);
        continue;
      }
      if (file.size > MAX_BYTES) {
        toast.error(`${file.name} is larger than 5 MB.`);
        continue;
      }
      const tile = { id: nextTile.current++, name: file.name };
      setUploading((u) => [...u, tile]);
      try {
        const photo = await hostingApi.uploadPhoto(listingId, file);
        onChange([...latest.current, photo]);
      } catch (error) {
        toast.error(error instanceof ApiError ? error.detail : `Could not upload ${file.name}.`);
      } finally {
        setUploading((u) => u.filter((t) => t.id !== tile.id));
      }
    }
  };

  const persistOrder = async (next: PhotoItem[]) => {
    const before = latest.current;
    onChange(next);
    try {
      onChange(await hostingApi.reorderPhotos(listingId, next.map((p) => p.id)));
    } catch (error) {
      onChange(before);
      toast.error(error instanceof ApiError ? error.detail : "Could not save the new order.");
    }
  };

  const move = (from: number, to: number) => {
    if (to < 0 || to >= photos.length || from === to) return;
    const next = [...photos];
    next.splice(to, 0, next.splice(from, 1)[0]);
    void persistOrder(next);
  };

  const remove = async (photo: PhotoItem) => {
    try {
      await hostingApi.deletePhoto(listingId, photo.id);
      onChange(photos.filter((p) => p.id !== photo.id));
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Could not remove the photo.");
    }
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setOver(false);
    if (event.dataTransfer.files.length > 0) void upload([...event.dataTransfer.files]);
  };

  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (dragged === null) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center gap-3 rounded-[16px] border-2 border-dashed px-6 py-10 text-center transition ${over ? "border-ink bg-surface" : "border-line"}`}
      >
        <ImagePlus size={40} strokeWidth={1.5} />
        <p className="text-lg font-semibold">Drag your photos here</p>
        <p className="text-sm text-muted">JPEG, PNG or WebP, up to 5 MB each. Choose at least {MIN_PHOTOS} photos.</p>
        <button type="button" onClick={() => input.current?.click()} className="font-semibold underline">
          Upload from your device
        </button>
        <input
          ref={input}
          type="file"
          multiple
          accept={ACCEPTED.join(",")}
          className="sr-only"
          aria-label="Upload photos"
          onChange={(event) => {
            void upload([...(event.target.files ?? [])]);
            event.target.value = "";
          }}
        />
      </div>

      {(photos.length > 0 || uploading.length > 0) && (
        <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
          {photos.map((photo, index) => (
            <li
              key={photo.id}
              draggable
              onDragStart={() => setDragged(index)}
              onDragEnd={() => setDragged(null)}
              onDragOver={(event) => dragged !== null && event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                if (dragged !== null) move(dragged, index);
                setDragged(null);
              }}
              className={`group relative overflow-hidden rounded-[12px] bg-surface ${index === 0 ? "col-span-2 row-span-2 sm:col-span-2" : ""}`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- local media through the proxy */}
              <img src={photo.card_url} alt={`Photo ${index + 1}`} className="aspect-[4/3] size-full cursor-grab object-cover" />
              {index === 0 && <span className="absolute left-2 top-2 rounded-full bg-white px-3 py-1 text-xs font-semibold shadow-pill">Cover photo</span>}
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-gradient-to-t from-black/60 to-transparent p-2 text-white opacity-100 sm:opacity-0 sm:transition sm:group-hover:opacity-100 sm:group-focus-within:opacity-100">
                <div className="flex gap-1">
                  <button type="button" aria-label="Move earlier" disabled={index === 0} onClick={() => move(index, index - 1)} className="grid size-8 place-items-center rounded-full bg-black/40 disabled:opacity-30">
                    <ArrowLeft size={14} />
                  </button>
                  <button type="button" aria-label="Move later" disabled={index === photos.length - 1} onClick={() => move(index, index + 1)} className="grid size-8 place-items-center rounded-full bg-black/40 disabled:opacity-30">
                    <ArrowRight size={14} />
                  </button>
                </div>
                <button type="button" aria-label="Delete photo" onClick={() => remove(photo)} className="grid size-8 place-items-center rounded-full bg-black/40">
                  <Trash2 size={14} />
                </button>
              </div>
            </li>
          ))}
          {uploading.map((tile) => (
            <li key={`up${tile.id}`} className="grid aspect-[4/3] place-items-center rounded-[12px] bg-surface text-sm text-muted">
              <span className="flex flex-col items-center gap-2 px-2 text-center">
                <Loader2 className="animate-spin" /> Uploading {tile.name}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-sm text-muted">
        {photos.length} photo{photos.length === 1 ? "" : "s"} · drag to reorder, the first one is your cover.
      </p>
    </div>
  );
}
