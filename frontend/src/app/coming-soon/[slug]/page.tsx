import Link from "next/link";

import { Button } from "@/components/ui/Button";

const TITLES: Record<string, string> = {
  messages: "Messages",
  help: "Help Centre",
  account: "Account",
  language: "Language and region",
  currency: "Currency",
  "gift-cards": "Gift cards",
  verification: "Identity verification",
  "forgot-password": "Reset your password",
};

const toTitle = (slug: string) =>
  TITLES[slug] ?? slug.replace(/-/g, " ").replace(/^\w/, (c) => c.toUpperCase());

/** Placeholder for features the project deliberately mocks (messaging, verification, help...). */
export default async function ComingSoonPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-[560px] flex-col items-center justify-center gap-5 px-6 py-20 text-center">
      <svg viewBox="0 0 120 120" className="size-28" aria-hidden>
        <circle cx="60" cy="60" r="56" fill="#fff1f3" />
        <path d="M60 28c2.6 0 4.5 1.3 6.2 4.3l.7 1.3c2.5 5 7.9 16.3 9.2 19.2l.2.5c.9 2 1.2 3.2 1.2 4.4 0 5.3-3.7 8.4-8.3 8.4-2.9 0-5.9-1.6-8.7-4.4-2.8 2.8-5.8 4.4-8.7 4.4-4.6 0-8.3-3.1-8.3-8.4 0-1.2.3-2.4 1.2-4.4l.2-.5c1.3-2.9 6.7-14.2 9.2-19.2l.7-1.3c1.7-3 3.6-4.3 6.2-4.3z" fill="none" stroke="#ff385c" strokeWidth="3" />
        <circle cx="60" cy="86" r="3" fill="#ff385c" />
      </svg>
      <h1 className="text-[32px] font-bold leading-tight">{toTitle(slug)}</h1>
      <p className="text-muted">
        This part of Airbnb is coming soon. In this version it is a placeholder, so there is nothing to see
        here yet.
      </p>
      <Link href="/">
        <Button size="lg">Back to explore</Button>
      </Link>
    </main>
  );
}
