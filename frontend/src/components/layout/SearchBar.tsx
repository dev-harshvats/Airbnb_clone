"use client";

import { MapPin, Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { DateRangePanel } from "@/components/search/DateRangePanel";
import { GuestPanel, type Guests } from "@/components/search/GuestPanel";
import { catalogApi } from "@/lib/api/catalog";
import { listingsApi } from "@/lib/api/listings";
import { formatRange } from "@/lib/format";
import { searchPath, type Section } from "@/lib/routes";
import { parseSearch, toSearchParams, type SearchState } from "@/lib/searchState";
import type { Destination, ServiceTypeSummary } from "@/types/api";

type SearchBarProps = {
  /** Which tab the bar belongs to; it changes the placeholders and the third segment. */
  section?: Section;
  initialWhere?: string;
  /** The search already in the URL, so editing dates or guests keeps the other filters. */
  initial?: SearchState;
  onDone?: () => void;
};

type Panel = "where" | "when" | "who" | "service" | null;

const NO_SEARCH = parseSearch(new URLSearchParams());

function guestSummary({ adults, children, infants, pets }: Guests) {
  const guests = adults + children;
  const parts = [guests ? `${guests} guest${guests > 1 ? "s" : ""}` : "", infants ? `${infants} infant${infants > 1 ? "s" : ""}` : "", pets ? `${pets} pet${pets > 1 ? "s" : ""}` : ""];
  return parts.filter(Boolean).join(", ") || "Add guests";
}

/**
 * The big three-segment search bar (Where / When / Who) with the red search button.
 * Homes get a destination dropdown, a two-month range calendar and guest steppers; Experiences search
 * "by city or landmark"; Services replace "Who" with "Type of service". Everything ends up in the URL.
 */
export function SearchBar({ section = "all", initialWhere = "", initial = NO_SEARCH, onDone }: SearchBarProps) {
  const [where, setWhere] = useState(initialWhere);
  const [panel, setPanel] = useState<Panel>(null);
  const [dates, setDates] = useState({ checkIn: initial.checkIn, checkOut: initial.checkOut });
  const [guests, setGuests] = useState<Guests>({ adults: initial.adults, children: initial.children, infants: initial.infants, pets: initial.pets });
  const [serviceType, setServiceType] = useState<ServiceTypeSummary | null>(null);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceTypeSummary[]>([]);
  const root = useRef<HTMLFormElement>(null);
  const router = useRouter();
  const services = section === "services";
  const experiences = section === "experiences";
  const homes = !services && !experiences;

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
    const place = location.trim() || null;
    if (homes) {
      // Keep the filters already on the page; only dates and guests come from this bar.
      router.push(searchPath("homes", place, toSearchParams({ ...initial, ...dates, ...guests })));
    } else {
      router.push(searchPath(section as "experiences" | "services", place, { service_type: services ? type?.key : undefined }));
    }
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    go(where);
  };
  const toggle = (next: Exclude<Panel, null>) => setPanel(panel === next ? null : next);

  const needle = where.trim().toLowerCase();
  const suggestions = destinations.filter((d) => !needle || `${d.city} ${d.state}`.toLowerCase().includes(needle));
  const hasDates = !!(dates.checkIn && dates.checkOut);
  const hasGuests = guests.adults + guests.children + guests.infants + guests.pets > 0;

  const segment =
    "flex h-full min-w-0 flex-col justify-center rounded-full text-left hover:bg-hover focus-within:bg-white focus-within:shadow-card";
  const open = "bg-white shadow-card";
  const label = "text-xs font-semibold";
  const popover = "absolute top-[74px] z-40 animate-pop rounded-[32px] bg-white p-6 shadow-modal";

  return (
    <form
      ref={root}
      onSubmit={submit}
      className="relative mx-auto flex h-[66px] w-full max-w-[850px] items-center rounded-full border border-line bg-white shadow-pill"
    >
      <label className={`${segment} flex-[1.3] cursor-text px-6 ${panel === "where" ? open : ""}`}>
        <span className={label}>Where</span>
        <input
          value={where}
          onChange={(e) => setWhere(e.target.value)}
          onFocus={() => setPanel("where")}
          placeholder={experiences ? "Search by city or landmark" : "Search destinations"}
          autoComplete="off"
          className="bg-transparent text-sm outline-none placeholder:text-muted"
        />
      </label>
      <span className="h-8 w-px bg-line" />
      <button
        type="button"
        className={`${segment} flex-1 px-6 ${panel === "when" ? open : ""}`}
        onClick={() => (homes ? toggle("when") : go(where))}
      >
        <span className={label}>{homes ? "Check in – out" : "When"}</span>
        <span className={`truncate text-sm ${hasDates ? "font-medium text-ink" : "text-muted"}`}>
          {hasDates ? formatRange(dates.checkIn!, dates.checkOut!) : "Add dates"}
        </span>
      </button>
      <span className="h-8 w-px bg-line" />
      {/* The last segment holds the text button and, at its right end, the round search button
          (48px, inset 10px from the bar's edge like airbnb.co.in). */}
      <div
        className={`flex h-full min-w-0 flex-1 items-center rounded-full pr-[9px] hover:bg-hover focus-within:bg-white focus-within:shadow-card ${panel === "who" || panel === "service" ? open : ""}`}
      >
        <button
          type="button"
          className="flex h-full min-w-0 flex-1 flex-col justify-center pl-6 text-left"
          onClick={() => (services ? toggle("service") : homes ? toggle("who") : go(where))}
        >
          <span className={label}>{services ? "Type of service" : "Who"}</span>
          <span className={`truncate text-sm ${(services ? serviceType : homes && hasGuests) ? "font-medium text-ink" : "text-muted"}`}>
            {services ? (serviceType?.label ?? "Add service") : homes ? guestSummary(guests) : "Add guests"}
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
        <div className={`${popover} left-0 w-[min(420px,100%)] !rounded-[32px] !p-4`}>
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

      {panel === "when" && (
        <div className={`${popover} left-1/2 w-max max-w-[calc(100vw-2rem)] -translate-x-1/2`}>
          <DateRangePanel checkIn={dates.checkIn} checkOut={dates.checkOut} onChange={(checkIn, checkOut) => setDates({ checkIn, checkOut })} />
          {(dates.checkIn || dates.checkOut) && (
            <button
              type="button"
              onClick={() => setDates({ checkIn: undefined, checkOut: undefined })}
              className="mt-2 flex items-center gap-1 text-sm font-semibold underline"
            >
              <X size={14} /> Clear dates
            </button>
          )}
        </div>
      )}

      {panel === "who" && (
        <div className={`${popover} right-0 w-[min(400px,100%)]`}>
          <GuestPanel value={guests} onChange={setGuests} />
        </div>
      )}

      {panel === "service" && (
        <div className={`${popover} right-0 w-[min(320px,100%)] !p-4`}>
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
