import type { Metadata } from "next";
import { Suspense } from "react";

import { ListingPage } from "@/components/listing/ListingPage";

export const metadata: Metadata = { title: "Airbnb | Stay" };

// `useSearchParams` (the trip dates) needs a Suspense boundary above it.
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <Suspense>
      <ListingPage id={id} />
    </Suspense>
  );
}
