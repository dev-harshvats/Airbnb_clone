"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DeleteListingDialog } from "@/components/host/DeleteListingDialog";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "@/components/ui/Toast";
import { hostingApi } from "@/lib/api/hosting";
import { formatINR, formatRange } from "@/lib/format";
import { useAuth } from "@/store/auth";
import type { HostListing, HostStats, Reservation } from "@/types/api";

type Tab = "today" | "listings" | "reservations" | "earnings";
const TABS: [Tab, string][] = [
  ["today", "Today"],
  ["listings", "Listings"],
  ["reservations", "Reservations"],
  ["earnings", "Earnings"],
];

type Data = { listings: HostListing[]; reservations: Reservation[]; stats: HostStats };

const STATUS = {
  active: ["Listed", "bg-[#e6f4ea] text-[#0a6b1f]"],
  inactive: ["Unlisted", "bg-surface text-muted"],
  draft: ["In progress", "bg-surface text-muted"],
} as const;

const isoDay = (date: Date) => date.toLocaleDateString("en-CA");
const addDays = (iso: string, days: number) => {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  return isoDay(d);
};

function ReservationRow({ r }: { r: Reservation }) {
  return (
    <li className="flex items-center gap-4 rounded-[12px] border border-line p-4">
      <Avatar firstName={r.guest_first_name} lastName={r.guest_last_initial} url={r.guest_avatar_url} size={44} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{r.guest_first_name} {r.guest_last_initial}.</p>
        <p className="truncate text-sm text-muted">{r.listing_title}</p>
      </div>
      <div className="text-right text-sm">
        <p className="font-medium">{formatRange(r.check_in, r.check_out)}</p>
        <p className="text-muted">{r.guests} guest{r.guests === 1 ? "" : "s"} · {formatINR(r.payout)}</p>
      </div>
    </li>
  );
}

function Today({ reservations }: { reservations: Reservation[] }) {
  const today = isoDay(new Date());
  const soon = addDays(today, 7);
  const live = reservations.filter((r) => r.status === "confirmed");
  const groups: [string, Reservation[]][] = [
    ["Checking out", live.filter((r) => r.check_out === today)],
    ["Currently hosting", live.filter((r) => r.check_in <= today && r.check_out > today)],
    ["Arriving soon", live.filter((r) => r.check_in > today && r.check_in <= soon)],
    ["Upcoming", live.filter((r) => r.check_in > soon)],
  ];
  const [tab, setTab] = useState(() => Math.max(0, groups.findIndex(([, items]) => items.length > 0)));
  const items = groups[tab][1];

  return (
    <div>
      <h2 className="mb-6 text-[22px] font-semibold">Your reservations</h2>
      <div role="tablist" className="no-scrollbar mb-6 flex gap-2 overflow-x-auto">
        {groups.map(([label, list], i) => (
          <button
            key={label}
            role="tab"
            aria-selected={tab === i}
            onClick={() => setTab(i)}
            className={`whitespace-nowrap rounded-full border px-4 py-2 text-sm font-medium transition ${tab === i ? "border-ink bg-ink text-canvas" : "border-line hover:border-ink"}`}
          >
            {label} ({list.length})
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <p className="rounded-[12px] bg-surface p-8 text-center text-muted">You don&apos;t have any guests {groups[tab][0].toLowerCase()}.</p>
      ) : (
        <ul className="space-y-3">{items.map((r) => <ReservationRow key={r.code} r={r} />)}</ul>
      )}
    </div>
  );
}

function Listings({ listings, onDelete }: { listings: HostListing[]; onDelete: (listing: HostListing) => void }) {
  if (listings.length === 0) {
    return (
      <div className="py-10 text-center">
        <h2 className="text-xl font-semibold">You don&apos;t have any listings yet</h2>
        <Link href="/become-a-host/about" className="mt-4 inline-block">
          <Button size="lg">Create a listing</Button>
        </Link>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-line text-muted">
          <tr>
            <th className="py-3 pr-4 font-medium">Listing</th>
            <th className="py-3 pr-4 font-medium">Status</th>
            <th className="py-3 pr-4 font-medium">Location</th>
            <th className="py-3 pr-4 font-medium">Price</th>
            <th className="py-3 pr-4 font-medium">Upcoming</th>
            <th className="py-3 font-medium"><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {listings.map((listing) => {
            const [label, tone] = STATUS[listing.status];
            return (
              <tr key={listing.id} className="border-b border-line-soft">
                <td className="py-4 pr-4">
                  <div className="flex items-center gap-3">
                    {listing.photo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element -- local media through the proxy
                      <img src={listing.photo_url} alt="" className="size-14 rounded-control object-cover" />
                    ) : (
                      <div className="size-14 rounded-control bg-surface" />
                    )}
                    <span className="max-w-[260px] truncate font-semibold">{listing.title}</span>
                  </div>
                </td>
                <td className="py-4 pr-4"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${tone}`}>{label}</span></td>
                <td className="py-4 pr-4">{listing.city}, {listing.state}</td>
                <td className="py-4 pr-4">{formatINR(listing.price_per_night)}</td>
                <td className="py-4 pr-4">{listing.upcoming_reservations}</td>
                <td className="py-4">
                  <div className="flex justify-end gap-4 font-semibold">
                    <Link href={`/hosting/listings/${listing.id}/edit`} className="underline">Edit</Link>
                    <button onClick={() => onDelete(listing)} className="underline">Delete</button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Reservations({ reservations }: { reservations: Reservation[] }) {
  const [filter, setFilter] = useState<"all" | "upcoming" | "past" | "cancelled">("all");
  const today = isoDay(new Date());
  const shown = reservations.filter((r) => {
    if (filter === "cancelled") return r.status === "cancelled";
    if (filter === "upcoming") return r.status === "confirmed" && r.check_out >= today;
    if (filter === "past") return r.status === "confirmed" && r.check_out < today;
    return true;
  });
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-[22px] font-semibold">{reservations.length} reservations</h2>
        <select aria-label="Filter reservations" value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)} className="h-10 rounded-control border border-line bg-canvas px-3 text-sm font-medium">
          <option value="all">All</option>
          <option value="upcoming">Upcoming</option>
          <option value="past">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      {shown.length === 0 ? (
        <p className="rounded-[12px] bg-surface p-8 text-center text-muted">No reservations here.</p>
      ) : (
        <div className="space-y-3">
          {shown.map((r) => (
            <div key={r.code}>
              <ul>
                <ReservationRow r={r} />
              </ul>
              <p className="px-2 pt-1 text-xs text-muted">{r.code} · {r.nights} night{r.nights === 1 ? "" : "s"} · {r.status === "cancelled" ? "Cancelled" : "Confirmed"}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Earnings({ stats, reservations }: { stats: HostStats; reservations: Reservation[] }) {
  const nights = reservations.filter((r) => r.status === "confirmed").reduce((sum, r) => sum + r.nights, 0);
  const tiles: [string, string][] = [
    ["Earned this month", formatINR(stats.earnings_this_month)],
    ["Total earned (completed stays)", formatINR(stats.earnings_total)],
    ["Upcoming reservations", String(stats.upcoming_reservations)],
    ["Active listings", String(stats.active_listings)],
    ["Total nights booked", String(nights)],
  ];
  return (
    <div>
      <h2 className="mb-6 text-[22px] font-semibold">Earnings</h2>
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map(([label, value]) => (
          <div key={label} className="rounded-[16px] border border-line p-6">
            <dt className="text-sm text-muted">{label}</dt>
            <dd className="mt-2 text-[32px] font-semibold leading-none">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-6 text-sm text-muted">Payouts shown are the nightly total plus cleaning fees, before Airbnb&apos;s service fee and taxes.</p>
    </div>
  );
}

/** /hosting: the host's home base. */
export function HostDashboard() {
  const [tab, setTab] = useState<Tab>("today");
  const [data, setData] = useState<Data | null>(null);
  const [failed, setFailed] = useState(false);
  const [deleting, setDeleting] = useState<HostListing | null>(null);
  const router = useRouter();
  const isHost = useAuth((s) => s.user?.is_host);

  // Only hosts have a dashboard; everyone else is sent to the "start hosting" page.
  useEffect(() => {
    if (isHost === false) router.replace("/host/homes");
  }, [isHost, router]);

  const load = () =>
    Promise.all([hostingApi.listings(), hostingApi.reservations(), hostingApi.stats()]).then(([listings, reservations, stats]) =>
      setData({ listings, reservations, stats }),
    );

  useEffect(() => {
    if (!isHost) return;
    let current = true;
    Promise.all([hostingApi.listings(), hostingApi.reservations(), hostingApi.stats()])
      .then(([listings, reservations, stats]) => current && setData({ listings, reservations, stats }))
      .catch(() => current && setFailed(true));
    return () => {
      current = false;
    };
  }, [isHost]);

  return (
    <main className="mx-auto max-w-[1120px] px-6 py-10">
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="text-[32px] font-semibold">Hosting</h1>
        <Link href="/become-a-host/about">
          <Button variant="secondary"><Plus size={16} /> Create listing</Button>
        </Link>
      </div>
      <div role="tablist" className="mb-8 flex gap-2 border-b border-line">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-4 pb-3 text-sm font-medium transition ${tab === key ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"}`}
          >
            {label}
          </button>
        ))}
      </div>

      {failed && <p className="text-muted">We couldn&apos;t load your dashboard. Please try again.</p>}
      {!data && !failed && <Skeleton className="h-64 w-full" />}
      {data && tab === "today" && <Today reservations={data.reservations} />}
      {data && tab === "listings" && <Listings listings={data.listings} onDelete={setDeleting} />}
      {data && tab === "reservations" && <Reservations reservations={data.reservations} />}
      {data && tab === "earnings" && <Earnings stats={data.stats} reservations={data.reservations} />}

      {deleting && (
        <DeleteListingDialog
          listing={deleting}
          onClose={() => setDeleting(null)}
          onDeleted={() => {
            setDeleting(null);
            toast.success("Listing deleted");
            void load();
          }}
          onUnlist={() => {
            const id = deleting.id;
            setDeleting(null);
            hostingApi
              .updateListing(id, { status: "inactive" })
              .then(() => load())
              .then(() => toast.success("Your listing is unlisted"))
              .catch(() => toast.error("We couldn't unlist that listing."));
          }}
        />
      )}
    </main>
  );
}
