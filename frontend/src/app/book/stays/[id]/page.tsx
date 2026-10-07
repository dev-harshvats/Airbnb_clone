import type { Metadata } from "next";
import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { CheckoutPage } from "@/components/booking/CheckoutPage";

export const metadata: Metadata = { title: "Confirm and pay" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <RequireAuth>
      <Suspense>
        <CheckoutPage id={id} />
      </Suspense>
    </RequireAuth>
  );
}
