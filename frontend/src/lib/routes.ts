/** URL conventions, matching airbnb.co.in: /s/{Place}/{homes|experiences|services}. */

export type Section = "all" | "homes" | "experiences" | "services";
export type Kind = Exclude<Section, "all">;

export const KINDS: Kind[] = ["homes", "experiences", "services"];
export const isKind = (value: string): value is Kind => (KINDS as string[]).includes(value);

/** "North Goa" -> "North-Goa" (and back), so a place is readable in the address bar. */
export const placeToSlug = (place: string) => place.trim().replace(/\s+/g, "-");

/** "Goa--India" and "Goa" both mean Goa; "North-Goa" means "North Goa". */
export const slugToPlace = (slug: string) => decodeURIComponent(slug).split("--")[0].replace(/-/g, " ").trim();

/** The search-results page for a kind of stay, optionally for one place. */
export function searchPath(kind: Kind, place?: string | null, query?: Record<string, string | undefined>): string {
  const base = place ? `/s/${encodeURIComponent(placeToSlug(place))}/${kind}` : `/s/${kind}`;
  const params = new URLSearchParams(Object.entries(query ?? {}).filter((e): e is [string, string] => !!e[1]));
  return params.size ? `${base}?${params}` : base;
}

/** Which tab of the header a path belongs to (the home page counts as "all"). */
export function sectionOf(pathname: string): Section {
  const [first, second, third] = pathname.split("/").filter(Boolean);
  if (!first) return "all";
  if (first === "homes" || first === "rooms") return "homes";
  if (first === "experiences") return "experiences";
  if (first === "services") return "services";
  if (first === "s") {
    if (isKind(second ?? "")) return second as Kind;
    if (isKind(third ?? "")) return third as Kind;
  }
  return "all";
}

/** The place in a /s/{place}/{kind} path, or null for /s/{kind} ("anywhere"). */
export function placeFromPath(pathname: string): string | null {
  const [first, second, third] = pathname.split("/").filter(Boolean);
  return first === "s" && third && isKind(third) ? slugToPlace(second) : null;
}

/** Only the four landing pages show the tall header with the big search bar. */
export const isLanding = (pathname: string) => ["/", "/homes", "/experiences", "/services"].includes(pathname);
