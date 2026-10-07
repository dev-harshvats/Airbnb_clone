"use client";

import { AlertCircle, CheckCircle2 } from "lucide-react";
import { create } from "zustand";

type ToastItem = {
  id: number;
  kind: "success" | "error";
  message: string;
  action?: { label: string; onClick: () => void };
};

type ToastStore = { items: ToastItem[]; push: (item: Omit<ToastItem, "id">) => void; dismiss: (id: number) => void };

const AUTO_DISMISS_MS = 4000;
let nextId = 1;

const useToastStore = create<ToastStore>((set, get) => ({
  items: [],
  push: (item) => {
    const id = nextId++;
    set({ items: [...get().items, { ...item, id }] });
    setTimeout(() => get().dismiss(id), AUTO_DISMISS_MS);
  },
  dismiss: (id) => set({ items: get().items.filter((t) => t.id !== id) }),
}));

/** Call from anywhere (event handlers, API callbacks): `toast.success("Saved to Wishlist")`. */
export const toast = {
  success: (message: string, action?: ToastItem["action"]) =>
    useToastStore.getState().push({ kind: "success", message, action }),
  error: (message: string) => useToastStore.getState().push({ kind: "error", message }),
};

/** Mount once in the root layout. Toasts sit bottom-left on desktop, bottom-centre on phones. */
export function Toaster() {
  const { items, dismiss } = useToastStore();
  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-4 bottom-20 z-[60] flex flex-col gap-2 md:inset-x-auto md:bottom-6 md:left-6"
    >
      {items.map((item) => (
        <div
          key={item.id}
          role="status"
          className="pointer-events-auto flex min-w-[280px] max-w-[420px] animate-slide-up items-center gap-3 rounded-[10px] bg-ink px-4 py-3.5 text-sm text-white shadow-modal"
        >
          {item.kind === "success" ? (
            <CheckCircle2 size={18} className="shrink-0" />
          ) : (
            <AlertCircle size={18} className="shrink-0 text-rausch" />
          )}
          <span className="flex-1">{item.message}</span>
          {item.action && (
            <button
              className="font-semibold underline underline-offset-2"
              onClick={() => {
                item.action?.onClick();
                dismiss(item.id);
              }}
            >
              {item.action.label}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
