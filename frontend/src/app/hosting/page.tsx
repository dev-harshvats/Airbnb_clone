import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { HostDashboard } from "@/components/host/HostDashboard";

export const metadata: Metadata = { title: "Hosting" };

export default function Page() {
  return (
    <RequireAuth>
      <HostDashboard />
    </RequireAuth>
  );
}
