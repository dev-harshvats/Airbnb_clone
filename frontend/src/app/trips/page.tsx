import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { TripsPage } from "@/components/booking/TripsPage";

export const metadata: Metadata = { title: "Trips" };

export default function Page() {
  return (
    <RequireAuth>
      <TripsPage />
    </RequireAuth>
  );
}
