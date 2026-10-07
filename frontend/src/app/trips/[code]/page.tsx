import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { TripDetailPage } from "@/components/booking/TripDetailPage";

export const metadata: Metadata = { title: "Trip" };

export default async function Page({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return (
    <RequireAuth>
      <TripDetailPage code={code} />
    </RequireAuth>
  );
}
