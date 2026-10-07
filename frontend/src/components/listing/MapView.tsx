"use client";

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Star, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import { MapContainer, Marker, TileLayer, useMap } from "react-leaflet";

import { formatINR } from "@/lib/format";
import { priceCaption } from "@/lib/listing";
import type { ListingCard } from "@/types/api";

const INDIA_CENTRE: [number, number] = [22.5, 79];

function pin(listing: ListingCard, active: boolean) {
  return L.divIcon({
    className: `price-pin${active ? " is-active" : ""}`,
    html: `<span>${formatINR(listing.price_per_night)}</span>`,
    iconSize: [0, 0],
  });
}

/** Re-frame the map around the pins whenever the result set changes. */
function FitToPins({ items }: { items: ListingCard[] }) {
  const map = useMap();
  useEffect(() => {
    if (items.length === 0) return;
    const bounds = L.latLngBounds(items.map((i) => [i.latitude, i.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 13 });
    // Only the first page of a search should re-frame; later pages add pins quietly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, items.length === 0, items[0]?.id]);
  // The map can be mounted while hidden (phones) or resized when the list is toggled.
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);
  return null;
}

type Props = {
  items: ListingCard[];
  selectedId: number | null;
  /** The card the pointer is over in the list, highlighted on the map. */
  hoverId?: number | null;
  onSelect: (id: number | null) => void;
  checkIn?: string;
  checkOut?: string;
  nights?: number;
};

/** Leaflet map with one price pill per listing; clicking a pill shows a small card for that stay. */
export default function MapView({ items, selectedId, hoverId = null, onSelect, nights }: Props) {
  const selected = items.find((i) => i.id === selectedId) ?? null;
  const icons = useMemo(
    () => new Map(items.map((i) => [i.id, pin(i, i.id === selectedId || i.id === hoverId)])),
    [items, selectedId, hoverId],
  );

  return (
    <div className="relative h-full w-full">
      <MapContainer center={INDIA_CENTRE} zoom={5} scrollWheelZoom className="h-full w-full" zoomControl>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={18}
        />
        <FitToPins items={items} />
        {items.map((listing) => (
          <Marker
            key={listing.id}
            position={[listing.latitude, listing.longitude]}
            icon={icons.get(listing.id)!}
            zIndexOffset={listing.id === selectedId || listing.id === hoverId ? 1000 : 0}
            eventHandlers={{ click: () => onSelect(listing.id) }}
          />
        ))}
      </MapContainer>

      {selected && (
        <div className="absolute inset-x-4 bottom-6 z-[1000] mx-auto flex max-w-[320px] animate-pop overflow-hidden rounded-[16px] bg-white shadow-modal">
          <button
            type="button"
            onClick={() => onSelect(null)}
            aria-label="Close"
            className="absolute right-2 top-2 z-10 grid size-7 place-items-center rounded-full bg-white/90 shadow hover:scale-105"
          >
            <X size={14} />
          </button>
          <Link href={`/rooms/${selected.id}`} className="flex w-full flex-col">
            {/* eslint-disable-next-line @next/next/no-img-element -- local media served through the proxy */}
            <img src={selected.photos[0]?.card_url} alt={selected.title} className="aspect-[16/10] w-full object-cover" />
            <div className="p-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <p className="truncate font-semibold">{selected.title}</p>
                {selected.rating_avg && (
                  <span className="flex shrink-0 items-center gap-1">
                    <Star size={12} className="fill-ink" /> {selected.rating_avg.toFixed(2)}
                  </span>
                )}
              </div>
              <p className="text-muted">{selected.city}, {selected.state}</p>
              <p className="mt-1">
                <span className="font-semibold">{priceCaption(selected, nights).amount}</span>{" "}
                <span className="text-muted">{priceCaption(selected, nights).suffix}</span>
              </p>
            </div>
          </Link>
        </div>
      )}
    </div>
  );
}
