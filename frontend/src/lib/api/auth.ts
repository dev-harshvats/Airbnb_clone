import { api, refreshSession } from "@/lib/api/client";
import type { AuthResponse, User } from "@/types/api";

export type SignupInput = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  date_of_birth: string; // YYYY-MM-DD
};

export const authApi = {
  emailExists: (email: string) =>
    api<{ exists: boolean }>("/auth/check-email", { method: "POST", body: { email } }).then((r) => r.exists),
  login: (email: string, password: string) =>
    api<AuthResponse>("/auth/login", { method: "POST", body: { email, password } }),
  signup: (input: SignupInput) => api<AuthResponse>("/auth/signup", { method: "POST", body: input }),
  /** Restore a session from the refresh cookie (rotates the cookie). */
  refresh: refreshSession,
  logout: () => api<void>("/auth/logout", { method: "POST" }),
  me: () => api<User>("/auth/me"),
};
