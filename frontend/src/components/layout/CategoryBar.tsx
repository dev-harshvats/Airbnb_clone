"use client";

import {
  Binoculars,
  Castle,
  ChevronLeft,
  ChevronRight,
  Droplets,
  Home,
  Landmark,
  MountainSnow,
  Palmtree,
  Sailboat,
  Sofa,
  Tent,
  TentTree,
  TreePine,
  Tractor,
  Waves,
  type LucideIcon,
} from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Skeleton } from "@/components/ui/Skeleton";
import { api } from "@/lib/api/client";
import { searchPath } from "@/lib/routes";
import type { Category } from "@/types/api";

// Backend `icon_key` -> icon. Unknown keys fall back to a house.
const ICONS: Record<string, LucideIcon> = {
  view: Binoculars,
  beach: Waves,
  cabin: TentTree,
  farm: Tractor,
  lake: Sailboat,
  mansion: Castle,
  countryside: Home,
  palm: Palmtree,
  treehouse: TreePine,
  heritage: Landmark,
  boat: Sailboat,
  pool: Droplets,
  tent: Tent,
  design: Sofa,
  tiny: Home,
  mountain: MountainSnow,
};

/** Sticky row of category icons under the header. The active category is the `category` URL param. */
export function CategoryBar({ place = null }: { place?: string | null }) {
  const [categories, setCategories] = useState<Category[] | null>(null);
  const [edges, setEdges] = useState({ left: false, right: true });
  const scroller = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const params = useSearchParams();
  const active = params.get("category");

  useEffect(() => {
    api<Category[]>("/categories")
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  const measure = () => {
    const el = scroller.current;
    if (el) setEdges({ left: el.scrollLeft > 4, right: el.scrollLeft + el.clientWidth < el.scrollWidth - 4 });
  };
  useEffect(measure, [categories]);

  const scrollBy = (direction: 1 | -1) =>
    scroller.current?.scrollBy({ left: direction * scroller.current.clientWidth * 0.8, behavior: "smooth" });

  const choose = (slug: string) => {
    const next = new URLSearchParams(params.toString());
    if (active === slug) next.delete("category");
    else next.set("category", slug);
    next.delete("page");
    router.push(searchPath("homes", place, Object.fromEntries(next)));
  };

  return (
    <div className="sticky top-[73px] z-20 border-b border-line-soft bg-white md:top-20">
      <div className="relative mx-auto max-w-[1760px] px-4 md:px-6 xl:px-20">
        {edges.left && (
          <button
            aria-label="Scroll categories left"
            onClick={() => scrollBy(-1)}
            className="absolute left-2 top-1/2 z-10 hidden size-8 -translate-y-1/2 place-items-center rounded-full border border-line bg-white shadow-pill hover:scale-105 md:grid xl:left-16"
          >
            <ChevronLeft size={14} />
          </button>
        )}
        <div ref={scroller} onScroll={measure} className="no-scrollbar flex gap-8 overflow-x-auto pt-3">
          {categories === null
            ? Array.from({ length: 12 }, (_, i) => (
                <div key={i} className="flex shrink-0 flex-col items-center gap-2 pb-3">
                  <Skeleton className="size-6 rounded-full" />
                  <Skeleton className="h-3 w-14" />
                </div>
              ))
            : categories.map((category) => {
                const Icon = ICONS[category.icon_key] ?? Home;
                const isActive = active === category.slug;
                return (
                  <button
                    key={category.id}
                    onClick={() => choose(category.slug)}
                    aria-pressed={isActive}
                    className={`group flex shrink-0 flex-col items-center gap-2 border-b-2 pb-3 text-xs font-semibold transition
                      ${isActive ? "border-ink text-ink" : "border-transparent text-muted hover:border-line hover:text-ink"}`}
                  >
                    <Icon size={24} strokeWidth={isActive ? 2 : 1.5} />
                    <span className="whitespace-nowrap">{category.label}</span>
                  </button>
                );
              })}
        </div>
        {edges.right && (
          <button
            aria-label="Scroll categories right"
            onClick={() => scrollBy(1)}
            className="absolute right-2 top-1/2 z-10 hidden size-8 -translate-y-1/2 place-items-center rounded-full border border-line bg-white shadow-pill hover:scale-105 md:grid xl:right-16"
          >
            <ChevronRight size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
