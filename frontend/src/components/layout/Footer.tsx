"use client";

import { Globe } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { hidesChrome, placeToSlug } from "@/lib/routes";

/** The footer's "Inspiration for future getaways" tabs: [place, what it is known for]. */
const INSPIRATION: Record<string, [place: string, note: string][]> = {
  Popular: [
    ["Goa", "Beach houses"], ["Jaipur", "Heritage stays"], ["Manali", "Mountain cottages"], ["Alleppey", "Houseboats"],
    ["Udaipur", "Lake views"], ["Rishikesh", "Riverside stays"], ["Munnar", "Tea-hill stays"], ["Mumbai", "City apartments"],
    ["Coorg", "Estate bungalows"], ["Leh", "Mountain guesthouses"], ["Pondicherry", "French Quarter"], ["Jaisalmer", "Desert camps"],
  ],
  Beach: [
    ["Anjuna", "Beach villas"], ["Palolem", "Beach cottages"], ["Gokarna", "Cliff-top stays"], ["Pondicherry", "Seaside houses"],
  ],
  Mountains: [
    ["Manali", "Cabins"], ["Shimla", "Colonial cottages"], ["Darjeeling", "Tea-garden stays"], ["Ooty", "Hill bungalows"], ["Leh", "Guesthouses"],
  ],
  Heritage: [
    ["Jaipur", "Havelis"], ["Udaipur", "Palace suites"], ["Jaisalmer", "Fort-view stays"], ["Varanasi", "Old-city stays"], ["Kochi", "Fort Kochi homes"],
  ],
  Backwaters: [
    ["Alleppey", "Houseboats"], ["Kochi", "Canal-side homes"], ["Munnar", "Plantation stays"],
  ],
};

const COLUMNS: { title: string; links: [label: string, href: string][] }[] = [
  {
    title: "Support",
    links: [
      ["Help Centre", "/help/home"],
      ["AirCover", "/aircover"],
      ["Anti-discrimination", "/against-discrimination"],
      ["Disability support", "/accessibility"],
      ["Cancellation options", "/help/home"],
      ["Report neighbourhood concern", "/neighbors"],
    ],
  },
  {
    title: "Hosting",
    links: [
      ["Airbnb your home", "/host/homes"],
      ["AirCover for Hosts", "/aircover-for-hosts"],
      ["Hosting resources", "/resources"],
      ["Community forum", "/t5/Community-Center/ct-p/community-center"],
      ["Hosting responsibly", "/help/responsible-hosting"],
      ["Join a free Hosting class", "/e/intro-to-hosting"],
      ["Find a co-host", "/host/co-hosts"],
    ],
  },
  {
    title: "Airbnb",
    links: [
      ["Newsroom", "/press/news"],
      ["New features", "/release"],
      ["Careers", "/careers"],
      ["Gift cards", "/gift-cards"],
      ["Refer a host", "/refer"],
    ],
  },
];

export function Footer() {
  const tabs = Object.keys(INSPIRATION);
  const [tab, setTab] = useState(tabs[0]);
  const pathname = usePathname();
  if (hidesChrome(pathname)) return null;

  return (
    <footer className="mt-12 border-t border-line bg-surface pb-24 text-sm md:pb-0">
      <div className="mx-auto max-w-[1760px] px-6 xl:px-20">
        <section className="border-b border-line py-10">
          <h2 className="mb-4 text-[22px] font-semibold">Inspiration for future getaways</h2>
          <div role="tablist" className="no-scrollbar mb-6 flex gap-6 overflow-x-auto border-b border-line">
            {tabs.map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={tab === name}
                onClick={() => setTab(name)}
                className={`-mb-px whitespace-nowrap border-b-2 pb-3 text-sm font-medium transition ${tab === name ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"}`}
              >
                {name}
              </button>
            ))}
          </div>
          <ul className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            {INSPIRATION[tab].map(([place, note]) => (
              <li key={place}>
                <Link href={`/${placeToSlug(place).toLowerCase()}/stays`} className="block hover:underline">
                  <span className="block font-medium">{place}</span>
                  <span className="font-light text-muted">{note}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <div className="grid grid-cols-1 gap-8 py-12 sm:grid-cols-3">
          {COLUMNS.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h3 className="mb-3 font-semibold">{column.title}</h3>
              <ul className="space-y-3">
                {column.links.map(([label, href]) => (
                  <li key={label}>
                    <Link href={href} className="font-light hover:underline">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="flex flex-col gap-4 border-t border-line py-6 md:flex-row md:items-center md:justify-between">
          <p className="flex flex-wrap items-center gap-x-2 font-light">
            <span>© 2026 Airbnb, Inc.</span>
            <span aria-hidden>·</span>
            <Link href="/terms/privacy_policy" className="hover:underline">Privacy</Link>
            <span aria-hidden>·</span>
            <Link href="/terms" className="hover:underline">Terms</Link>
            <span aria-hidden>·</span>
            <Link href="/about/company-details" className="hover:underline">Company details</Link>
          </p>
          <div className="flex items-center gap-6 font-semibold">
            <Link href="/coming-soon/language" className="flex items-center gap-2 hover:underline">
              <Globe size={16} /> English (IN)
            </Link>
            <Link href="/coming-soon/currency" className="hover:underline">₹ INR</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
