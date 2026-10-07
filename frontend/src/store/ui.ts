import { create } from "zustand";

type UiState = {
  authModalOpen: boolean;
  /** Where to go once the user has logged in (set when a protected page asked for a login). */
  redirectAfterAuth: string | null;
  /** Called if the login modal is dismissed without logging in. */
  onAuthCancel: (() => void) | null;
  openAuth: (options?: { redirectTo?: string; onCancel?: () => void }) => void;
  closeAuth: (reason?: "success" | "dismiss") => void;
  /** The listing whose "Save to wishlist" dialog is open, if any. */
  saveListingId: number | null;
  openSave: (listingId: number) => void;
  closeSave: () => void;
  searchExpanded: boolean;
  setSearchExpanded: (open: boolean) => void;
};

export const useUi = create<UiState>((set, get) => ({
  authModalOpen: false,
  redirectAfterAuth: null,
  onAuthCancel: null,
  openAuth: (options) =>
    set({
      authModalOpen: true,
      redirectAfterAuth: options?.redirectTo ?? null,
      onAuthCancel: options?.onCancel ?? null,
    }),
  closeAuth: (reason = "dismiss") => {
    const { onAuthCancel } = get();
    set({ authModalOpen: false, onAuthCancel: null });
    if (reason === "dismiss") onAuthCancel?.();
  },
  saveListingId: null,
  openSave: (listingId) => set({ saveListingId: listingId }),
  closeSave: () => set({ saveListingId: null }),
  searchExpanded: false,
  setSearchExpanded: (open) => set({ searchExpanded: open }),
}));
