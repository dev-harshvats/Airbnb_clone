import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { ListingEditor } from "@/components/host/ListingEditor";

export const metadata: Metadata = { title: "Edit listing" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const id = Number((await params).id);
  if (!Number.isInteger(id) || id < 1) notFound();
  return (
    <RequireAuth>
      <ListingEditor id={id} />
    </RequireAuth>
  );
}
