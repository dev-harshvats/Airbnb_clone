"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { SearchBar } from "@/components/layout/SearchBar";
import { MobileSearchPill } from "@/components/layout/SearchPill";
import { BalloonIcon, BellIcon, GlobeIcon, HouseIcon } from "@/components/layout/TabIcons";
import { AccountControls } from "@/components/layout/UserMenu";
import { Logo } from "@/components/ui/Logo";
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
 * bar underneath. Every other page gets a compact bar whose small pill opens the full search.
 */
export function Header() {
  const pathname = usePathname();
  if (hidesChrome(pathname)) return null;
  return (
    <>
      <div className="md:hidden">
        <header className="sticky top-0 z-30 border-b border-line-soft bg-white px-4 py-3">
          <MobileSearchPill />
        </header>
      </div>
      <div className="hidden md:block">
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

function LandingHeader({ section }: { section: Section }) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface">
      <div className="mx-auto grid h-20 max-w-[1760px] grid-cols-[1fr_auto_1fr] items-center px-6 xl:px-20">
        <Link href="/" aria-label="Airbnb home">
          <Logo compactOnSmallScreens />
        </Link>
        <nav aria-label="Browse" className="flex items-center gap-2">
          {TABS.map(({ section: tab, label, href, Icon }) => {
            const active = tab === section;
            return (
              <Link
                key={tab}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`relative flex items-center gap-1.5 rounded-full px-4 py-2 text-sm transition hover:bg-hover ${active ? "font-semibold text-ink" : "text-muted"}`}
              >
                <Icon className={`size-9 transition ${active ? "" : "opacity-60 grayscale"}`} />
                {label}
                {active && <span className="absolute inset-x-4 -bottom-1 h-0.5 rounded bg-ink" />}
              </Link>
            );
          })}
        </nav>
        <div className="justify-self-end">
          <AccountControls />
        </div>
      </div>
      <div className="px-6 pb-6">
        {/* keyed by section so the field state resets when you switch tabs */}
        <SearchBar key={section} section={section} />
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
    <header ref={root} className="sticky top-0 z-30 border-b border-line-soft bg-white">
      <div className="mx-auto grid h-20 max-w-[1760px] grid-cols-[1fr_auto_1fr] items-center px-6 xl:px-20">
        <Link href="/" aria-label="Airbnb home">
          <Logo compactOnSmallScreens />
        </Link>
        <button
          onClick={() => setOpen(true)}
          aria-label="Start your search"
          className="flex h-12 items-center rounded-full border border-line bg-white pl-2 pr-2 text-sm shadow-pill transition hover:shadow-card"
        >
          <span className="px-4 font-semibold">{location ? `${noun} in ${location}` : "Anywhere"}</span>
          <span className="h-6 w-px bg-line" />
          <span className="px-4 font-semibold">{checkIn && checkOut ? formatRange(checkIn, checkOut) : "Any week"}</span>
          <span className="h-6 w-px bg-line" />
          <span className={`pl-4 pr-3 ${guests ? "font-semibold" : "text-muted"}`}>
            {section === "services" ? "Add service" : guests ? `${guests} guest${guests > 1 ? "s" : ""}` : "Add guests"}
          </span>
          <span className="grid size-8 place-items-center rounded-full bg-rausch text-white">
            <Search size={14} strokeWidth={3} />
          </span>
        </button>
        <div className="justify-self-end">
          <AccountControls />
        </div>
      </div>
      {open && (
        <div className="animate-fade-in border-t border-line-soft bg-surface px-6 pb-6 pt-5">
          <SearchBar section={section} initialWhere={location ?? ""} initial={parseSearch(params)} onDone={() => setOpen(false)} />
        </div>
      )}
    </header>
  );
}
