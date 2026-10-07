import { redirect } from "next/navigation";

import { searchPath } from "@/lib/routes";

/** Old address from the first version of this app: forward to the Airbnb-style route. */
export default async function LegacySearchPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const { location, ...rest } = await searchParams;
  redirect(searchPath("homes", location, rest));
}
