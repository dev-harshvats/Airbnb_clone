"use client";

import { X } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

type ModalProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  /** Optional element on the left of the header (for example a back arrow). */
  headerLeft?: ReactNode;
  className?: string;
};

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

/**
 * Airbnb-style dialog: a centred card on desktop and a bottom sheet on phones. Closes on Escape or
 * a click outside, keeps keyboard focus inside while open, and returns focus when it closes.
 */
export function Modal({ open, onClose, title, children, headerLeft, className = "" }: ModalProps) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const scrollbar = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${scrollbar}px`;
    const firstField = panel.current?.querySelector<HTMLElement>("input, textarea, select");
    (firstField ?? panel.current?.querySelector<HTMLElement>(FOCUSABLE))?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") return onClose();
      if (event.key !== "Tab" || !panel.current) return;
      const items = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      document.body.style.paddingRight = "";
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 animate-fade-in md:items-center"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-[20px] bg-white shadow-modal
          animate-slide-up md:max-w-[568px] md:animate-pop md:rounded-[12px] ${className}`}
      >
        <header className="relative flex h-16 shrink-0 items-center justify-center border-b border-line-soft px-6">
          <div className="absolute left-4 flex">
            {headerLeft ?? (
              <button
                onClick={onClose}
                aria-label="Close"
                className="grid size-8 place-items-center rounded-full hover:bg-surface"
              >
                <X size={16} />
              </button>
            )}
          </div>
          {title && <h2 className="text-base font-bold">{title}</h2>}
        </header>
        <div className="overflow-y-auto">{children}</div>
      </div>
    </div>,
    document.body,
  );
}
