"use client";

import { ArrowRight, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

type ScrollRowProps = {
  title: string;
  subtitle?: string;
  /** Makes the heading a link with Airbnb's small arrow button (for example to a search). */
  href?: string;
  children: ReactNode;
};

const arrowButton =
  "grid size-8 place-items-center rounded-full border border-line bg-white shadow-pill transition hover:scale-105 hover:shadow-card disabled:cursor-default disabled:opacity-30 disabled:hover:scale-100 disabled:hover:shadow-pill";

/** A titled, horizontally scrolling row with round previous/next buttons. */
export function ScrollRow({ title, subtitle, href, children }: ScrollRowProps) {
  const scroller = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ start: true, end: false });

  const measure = useCallback(() => {
    const el = scroller.current;
    if (el) setEdges({ start: el.scrollLeft < 4, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4 });
  }, []);

  useEffect(() => {
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [measure, children]);

  const scrollBy = (direction: 1 | -1) =>
    scroller.current?.scrollBy({ left: direction * scroller.current.clientWidth * 0.85, behavior: "smooth" });

  const heading = (
    <h2 className="flex items-center gap-2 text-[22px] font-semibold leading-tight">
      {title}
      {href && (
        <span className="grid size-6 place-items-center rounded-full bg-surface">
          <ArrowRight size={14} />
        </span>
      )}
    </h2>
  );

  return (
    <section className="py-6">
      <div className="mb-4 flex items-end justify-between">
        <div>
          {href ? <Link href={href}>{heading}</Link> : heading}
          {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
        </div>
        <div className="hidden gap-2 md:flex">
          <button aria-label="Previous" disabled={edges.start} onClick={() => scrollBy(-1)} className={arrowButton}>
            <ChevronLeft size={14} />
          </button>
          <button aria-label="Next" disabled={edges.end} onClick={() => scrollBy(1)} className={arrowButton}>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
      <div ref={scroller} onScroll={measure} className="no-scrollbar -mx-1 flex snap-x gap-4 overflow-x-auto px-1 pb-1 md:gap-5">
        {children}
      </div>
    </section>
  );
}
