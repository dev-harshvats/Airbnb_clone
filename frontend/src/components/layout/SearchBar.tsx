"use client";

import { MapPin, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { catalogApi } from "@/lib/api/catalog";
import { listingsApi } from "@/lib/api/listings";
import { searchPath, type Section } from "@/lib/routes";
import type { Destination, ServiceTypeSummary } from "@/types/api";

type SearchBarProps = {
  /** Which tab the bar belongs to; it changes the placeholders and the third segment. */
  section?: Section;
  initialWhere?: string;
  onDone?: () => void;
};

type Panel = "where" | "service" | null;

/**
 * The big three-segment search bar (Where / When / Who) with the red search button.
 * Experiences search "by city or landmark"; Services replace "Who" with "Type of service".
 * "Where" is a live field with a dropdown of destinations; the date and guest panels come with the
 * explore step.
 */
export function SearchBar({ section = "all", initialWhere = "", onDone }: SearchBarProps) {
  const [where, setWhere] = useState(initialWhere);
  const [panel, setPanel] = useState<Panel>(null);
  const [serviceType, setServiceType] = useState<ServiceTypeSummary | null>(null);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceTypeSummary[]>([]);
  const root = useRef<HTMLFormElement>(null);
  const router = useRouter();
  const services = section === "services";

  useEffect(() => {
    listingsApi.destinations().then(setDestinations).catch(() => setDestinations([]));
  }, []);
  useEffect(() => {
    if (services) catalogApi.serviceTypes().then(setServiceTypes).catch(() => setServiceTypes([]));
  }, [services]);

  useEffect(() => {
    if (!panel) return;
    const close = (event: MouseEvent) => !root.current?.contains(event.target as Node) && setPanel(null);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [panel]);

  const go = (location: string, type: ServiceTypeSummary | null = serviceType) => {
    setPanel(null);
    onDone?.();
    const kind = section === "all" ? "homes" : section;
    router.push(searchPath(kind, location.trim() || null, { service_type: services ? type?.key : undefined }));
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    go(where);
  };

  const needle = where.trim().toLowerCase();
  const suggestions = destinations.filter((d) => !needle || `${d.city} ${d.state}`.toLowerCase().includes(needle));

  const segment =
    "flex h-full min-w-0 flex-col justify-center rounded-full text-left hover:bg-[#ebebeb] focus-within:bg-white focus-within:shadow-card";
  const label = "text-xs font-semibold";

  return (
    <form
      ref={root}
      onSubmit={submit}
      className="relative mx-auto flex h-16 w-full max-w-[850px] items-center rounded-full border border-line bg-white shadow-pill"
    >
      <label className={`${segment} flex-[1.3] cursor-text px-6`}>
        <span className={label}>Where</span>
        <input
          value={where}
          onChange={(e) => setWhere(e.target.value)}
          onFocus={() => setPanel("where")}
          placeholder={section === "experiences" ? "Search by city or landmark" : "Search destinations"}
          autoComplete="off"
          className="bg-transparent text-sm outline-none placeholder:text-muted"
        />
      </label>
      <span className="h-8 w-px bg-line" />
      <button type="button" className={`${segment} flex-1 px-6`} onClick={() => go(where)}>
        <span className={label}>When</span>
        <span className="text-sm text-muted">Add dates</span>
      </button>
      <span className="h-8 w-px bg-line" />
      <div className={`${segment} flex-1 flex-row items-center justify-between pl-6 pr-2`}>
        <button
          type="button"
          className="flex min-w-0 flex-col text-left"
          onClick={() => (services ? setPanel(panel === "service" ? null : "service") : go(where))}
        >
          <span className={label}>{services ? "Type of service" : "Who"}</span>
          <span className={`truncate text-sm ${serviceType ? "font-medium text-ink" : "text-muted"}`}>
            {services ? (serviceType?.label ?? "Add service") : "Add guests"}
          </span>
        </button>
        <button
          type="submit"
          aria-label="Search"
          className="grid size-12 shrink-0 place-items-center rounded-full bg-rausch text-white transition hover:bg-rausch-dark"
        >
          <Search size={18} strokeWidth={3} />
        </button>
      </div>

      {panel === "where" && suggestions.length > 0 && (
        <div className="absolute left-0 top-[72px] z-40 w-[min(420px,100%)] animate-pop rounded-[32px] bg-white p-4 shadow-modal">
          <p className="px-3 pb-2 pt-1 text-xs font-semibold">{needle ? "Destinations" : "Suggested destinations"}</p>
          <ul>
            {suggestions.slice(0, 7).map((d) => (
              <li key={`${d.city}-${d.state}`}>
                <button
                  type="button"
                  onClick={() => go(d.city)}
                  className="flex w-full items-center gap-4 rounded-control px-3 py-2.5 text-left hover:bg-surface"
                >
                  <span className="grid size-12 place-items-center rounded-control bg-surface">
                    <MapPin size={20} />
                  </span>
                  <span className="text-sm">
                    <span className="block font-medium">
                      {d.city}, {d.state}
                    </span>
                    <span className="text-muted">{d.listing_count} stays</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {panel === "service" && (
        <div className="absolute right-0 top-[72px] z-40 w-[min(320px,100%)] animate-pop rounded-[32px] bg-white p-4 shadow-modal">
          <p className="px-3 pb-2 pt-1 text-xs font-semibold">Type of service</p>
          <ul>
            {serviceTypes.map((type) => (
              <li key={type.key}>
                <button
                  type="button"
                  onClick={() => {
                    setServiceType(type);
                    go(where, type);
                  }}
                  className="flex w-full items-center justify-between rounded-control px-3 py-3 text-left text-sm hover:bg-surface"
                >
                  <span className="font-medium">{type.label}</span>
                  <span className="text-muted">{type.count}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}
