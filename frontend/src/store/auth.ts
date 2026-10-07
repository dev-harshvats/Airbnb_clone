import { create } from "zustand";

import { authApi, type SignupInput } from "@/lib/api/auth";
import { configureApi } from "@/lib/api/client";
import type { AuthResponse, User } from "@/types/api";

/**
 * The access token lives only in memory (never localStorage), so a page reload or an injected
 * script cannot read it. After a reload the HttpOnly refresh cookie restores the session.
 * `HINT_KEY` just remembers that a session existed, so first-time visitors don't make a
 * pointless refresh call on every page load.
 */
const HINT_KEY = "airbnb:has-session";

const hint = {
  get: () => {
    try {
      return localStorage.getItem(HINT_KEY) === "1";
    } catch {
      return false;
    }
  },
  set: (on: boolean) => {
    try {
      if (on) localStorage.setItem(HINT_KEY, "1");
      else localStorage.removeItem(HINT_KEY);
    } catch {
      /* storage unavailable (private mode): the session simply will not survive a reload */
    }
  },
};

type AuthState = {
  user: User | null;
  accessToken: string | null;
  /** "loading" until the first session check finishes, so pages don't flash a logged-out UI. */
  status: "loading" | "authed" | "anon";
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<User>;
  signup: (input: SignupInput) => Promise<User>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
};

export const useAuth = create<AuthState>((set, get) => {
  const startSession = (session: AuthResponse) => {
    hint.set(true);
    set({ user: session.user, accessToken: session.access_token, status: "authed" });
    return session.user;
  };
  const endSession = () => {
    hint.set(false);
    set({ user: null, accessToken: null, status: "anon" });
  };

  return {
    user: null,
    accessToken: null,
    status: "loading",

    async bootstrap() {
      if (get().status !== "loading") return;
      if (!hint.get()) return set({ status: "anon" });
      try {
        startSession(await authApi.refresh());
      } catch {
        endSession();
      }
    },

    login: async (email, password) => startSession(await authApi.login(email, password)),
    signup: async (input) => startSession(await authApi.signup(input)),

    async logout() {
      try {
        await authApi.logout();
      } finally {
        endSession(); // even if the network call fails, this browser is logged out
      }
    },

    updateUser: (user) => set({ user }),
  };
});

// Wire the API client to this store once, when the module loads.
configureApi({
  getToken: () => useAuth.getState().accessToken,
  onRefreshed: (session) =>
    useAuth.setState({ user: session.user, accessToken: session.access_token, status: "authed" }),
  onSessionLost: () => {
    hint.set(false);
    useAuth.setState({ user: null, accessToken: null, status: "anon" });
  },
});
