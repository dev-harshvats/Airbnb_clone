"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState, type ReactNode } from "react";

import { SearchBar } from "@/components/layout/SearchBar";
import { MobileSearchPill } from "@/components/layout/SearchPill";
import { BalloonIcon, BellIcon, GlobeIcon, HouseIcon } from "@/components/layout/TabIcons";
import { AccountControls } from "@/components/layout/UserMenu";
import { Logo } from "@/components/ui/Logo";
import { useScrollCollapsed } from "@/hooks/useScrollCollapsed";
import { formatRange } from "@/lib/format";
import { hidesChrome, isLanding, placeFromPath, sectionOf, type Section } from "@/lib/routes";
import { parseSearch } from "@/lib/searchState";

const TABS: { section: Section; label: string; href: string; Icon: typeof GlobeIcon }[] = [
  { section: "all", label: "All", href: "/", Icon: GlobeIcon },
  { section: "homes", label: "Homes", href: "/homes", Icon: HouseIcon },
  { section: "experiences", label: "Experiences", href: "/experiences", Icon: BalloonIcon },
  { section: "services", label: "Services", href: "/services", Icon: BellIcon },
];

const SECTION_NOUN: Record<Section, string> = {
  all: "Homes",
  homes: "Homes",
  experiences: "Experiences",
  services: "Services",
};

/**
 * The four landing pages (/, /homes, /experiences, /services) show the tab row with the big search
 * bar underneath, and fold it into the compact bar when you scroll. Every other page starts with the
 * compact bar, whose pill unfolds the full search.
 */
export function Header() {
  const pathname = usePathname();
  if (hidesChrome(pathname)) return null;
  return (
    <>
      <div className="contents md:hidden">
        <header className="sticky top-0 z-30 border-b border-line-soft bg-white px-4 py-3">
          <MobileSearchPill />
        </header>
      </div>
      <div className="hidden md:contents">
        {isLanding(pathname) ? (
          <LandingHeader section={sectionOf(pathname)} />
        ) : (
          <Suspense fallback={<div className="h-20 border-b border-line-soft" />}>
            <CompactHeader section={sectionOf(pathname)} />
          </Suspense>
        )}
      </div>
    </>
  );
}

/** The folded-up search: a small pill that unfolds the big bar when clicked. */
function Pill({ icon, parts, onClick }: { icon?: ReactNode; parts: [string, string, ReactNode]; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label="Start your search"
      className="hdr-pill absolute left-1/2 top-1/2 flex h-12 -translate-x-1/2 -translate-y-1/2 items-center rounded-full border border-line bg-white pl-2 pr-2 text-sm shadow-pill transition-shadow duration-200 hover:shadow-card"
    >
      {icon}
      <span className="whitespace-nowrap px-4 font-semibold">{parts[0]}</span>
      <span className="h-6 w-px bg-line" />
      <span className="whitespace-nowrap px-4 font-semibold">{parts[1]}</span>
      <span className="h-6 w-px bg-line" />
      <span className="whitespace-nowrap pl-4 pr-3">{parts[2]}</span>
      <span className="grid size-8 place-items-center rounded-full bg-rausch text-white">
        <Search size={14} strokeWidth={3} />
      </span>
    </button>
  );
}

/** Keeps a header that was opened by hand open until the page is scrolled a little, then closes it. */
function useCloseOnScroll(open: boolean, close: () => void) {
  useEffect(() => {
    if (!open) return;
    const startedAt = window.scrollY;
    const onScroll = () => Math.abs(window.scrollY - startedAt) > 16 && close();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [open, close]);
}

function LandingHeader({ section }: { section: Section }) {
  const scrolled = useScrollCollapsed();
  const [opened, setOpened] = useState(false);
  // Opened by hand, the full bar stays until the next scroll; otherwise it simply follows the scroll position.
  const expanded = !scrolled || opened;
  const Current = TABS.find((t) => t.section === section)?.Icon ?? GlobeIcon;

  useCloseOnScroll(opened, () => setOpened(false));

  return (
    <header
      data-expanded={expanded}
      className={`hdr sticky top-0 z-30 border-b ${expanded ? "border-line bg-surface" : "border-line-soft bg-white"}`}
    >
      <div className="mx-auto grid h-20 max-w-[1760px] grid-cols-[1fr_auto_1fr] items-center px-8 xl:px-20">
        <Link href="/" aria-label="Airbnb home" className="flex items-center">
          <Logo compactOnSmallScreens />
        </Link>
        <div className="relative flex h-full min-w-[380px] items-center justify-center">
          <nav aria-label="Browse" inert={!expanded} className="hdr-tabs flex items-center gap-2">
            {TABS.map(({ section: tab, label, href, Icon }) => {
              const active = tab === section;
              return (
                <Link
                  key={tab}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`tab-link relative flex items-center gap-1.5 rounded-full px-4 py-2 text-sm transition-colors duration-200 hover:bg-hover ${active ? "font-semibold text-ink" : "text-muted hover:text-ink"}`}
                >
                  <Icon className={`size-9 transition duration-300 ${active ? "" : "opacity-60 grayscale"}`} />
                  {label}
                  {active && <span className="absolute inset-x-4 -bottom-1 h-0.5 animate-underline rounded bg-ink" />}
                </Link>
              );
            })}
          </nav>
          <Pill
            icon={<Current className="size-8" />}
            parts={["Anywhere", "Anytime", <span key="who" className="text-muted">{section === "services" ? "Add service" : "Add guests"}</span>]}
            onClick={() => setOpened(true)}
          />
        </div>
        <div className="justify-self-end">
          <AccountControls />
        </div>
      </div>
      <div className={`reveal ${expanded ? "is-open" : ""}`} inert={!expanded}>
        <div className="reveal-inner">
          {/* keyed by section so the field state resets when you switch tabs */}
          <div className="bar-morph px-6 pb-6">
            <SearchBar key={section} section={section} />
          </div>
        </div>
      </div>
    </header>
  );
}

function CompactHeader({ section }: { section: Section }) {
  const pathname = usePathname();
  const params = useSearchParams();
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    const outside = (event: MouseEvent) => !root.current?.contains(event.target as Node) && close();
    const escape = (event: KeyboardEvent) => event.key === "Escape" && close();
    window.addEventListener("scroll", close, { passive: true });
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      window.removeEventListener("scroll", close);
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  const location = placeFromPath(pathname) ?? params.get("location");
  const checkIn = params.get("check_in");
  const checkOut = params.get("check_out");
  const guests = Number(params.get("adults") ?? 0) + Number(params.get("children") ?? 0);
  const noun = SECTION_NOUN[section];

  return (
    <header ref={root} data-expanded={open} className={`hdr sticky top-0 z-30 border-b ${open ? "border-line bg-surface" : "border-line-soft bg-white"}`}>
      <div className="mx-auto grid h-20 max-w-[1760px] grid-cols-[1fr_auto_1fr] items-center px-8 xl:px-20">
        <Link href="/" aria-label="Airbnb home" className="flex items-center">
          <Logo compactOnSmallScreens />
        </Link>
        <div className="relative h-full min-w-[420px]">
          <Pill
            parts={[
              location ? `${noun} in ${location}` : "Anywhere",
              checkIn && checkOut ? formatRange(checkIn, checkOut) : "Any week",
              <span key="who" className={guests ? "font-semibold" : "text-muted"}>
                {section === "services" ? "Add service" : guests ? `${guests} guest${guests > 1 ? "s" : ""}` : "Add guests"}
              </span>,
            ]}
            onClick={() => setOpen(true)}
          />
        </div>
        <div className="justify-self-end">
          <AccountControls />
        </div>
      </div>
      <div className={`reveal ${open ? "is-open" : ""}`} inert={!open}>
        <div className="reveal-inner">
          <div className="bar-morph px-6 pb-6 pt-1">
            {/* keyed by the URL so the fields start from the current search after every navigation */}
            <SearchBar
              key={`${pathname}?${params}`}
              section={section}
              initialWhere={location ?? ""}
              initial={parseSearch(params)}
              onDone={() => setOpen(false)}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
