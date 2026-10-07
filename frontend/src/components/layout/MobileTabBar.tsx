"use client";

import { Heart, Search, UserCircle } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BeloIcon } from "@/components/ui/Logo";
import { hidesChrome } from "@/lib/routes";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

/** Bottom navigation for phones (below 744px), like the Airbnb app. */
export function MobileTabBar() {
  const pathname = usePathname();
  const { status } = useAuth();
  const openAuth = useUi((s) => s.openAuth);
  const authed = status === "authed";
  // Detail and checkout pages have their own sticky bottom bar.
  if (/^\/(rooms|book)\//.test(pathname) || hidesChrome(pathname)) return null;

  const tab = (active: boolean) =>
    `flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium ${active ? "text-rausch" : "text-muted"}`;

  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-white md:hidden">
      <Link href="/" className={tab(pathname === "/")}>
        <Search size={22} /> Explore
      </Link>
      <Link href="/wishlists" className={tab(pathname.startsWith("/wishlists"))}>
        <Heart size={22} /> Wishlists
      </Link>
      <Link href="/trips" className={tab(pathname.startsWith("/trips"))}>
        <BeloIcon className="size-[22px]" /> Trips
      </Link>
      {status === "loading" ? (
        <span className={tab(false)}>
          <UserCircle size={22} /> Profile
        </span>
      ) : authed ? (
        <Link href="/coming-soon/account" className={tab(pathname.startsWith("/coming-soon/account"))}>
          <UserCircle size={22} /> Profile
        </Link>
      ) : (
        <button onClick={() => openAuth()} className={tab(false)}>
          <UserCircle size={22} /> Log in
        </button>
      )}
    </nav>
  );
}
