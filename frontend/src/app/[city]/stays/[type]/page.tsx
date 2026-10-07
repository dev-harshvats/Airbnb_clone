import { redirect } from "next/navigation";

import { searchPath, slugToPlace } from "@/lib/routes";

const PROPERTY_TYPE: Record<string, string> = {
  houses: "house",
  apartments: "flat",
  condos: "flat",
  cabins: "cabin",
  villas: "villa",
  cottages: "cottage",
};

/** /{city}/stays/{type} (for example /goa/stays/villas) forwards to filtered results. */
export default async function CityStayTypePage({ params }: { params: Promise<{ city: string; type: string }> }) {
  const { city, type } = await params;
  redirect(searchPath("homes", slugToPlace(city), { property_types: PROPERTY_TYPE[type] }));
}
