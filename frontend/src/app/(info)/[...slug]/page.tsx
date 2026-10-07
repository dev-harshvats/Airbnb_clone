import Link from "next/link";
import { notFound } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { INFO_PAGES } from "@/lib/infoPages";

/** Placeholder pages that keep the original site's URLs (help, hosting, company, legal). */
export default async function InfoPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const page = INFO_PAGES[(await params).slug.join("/")];
  if (!page) notFound();
  return (
    <main className="mx-auto flex min-h-[55vh] max-w-[560px] flex-col items-center justify-center gap-5 px-6 py-20 text-center">
      <h1 className="text-[32px] font-bold leading-tight">{page.title}</h1>
      <p className="text-muted">
        {page.blurb ? `${page.blurb} ` : ""}This part of Airbnb is coming soon. In this version it is a placeholder.
      </p>
      <Link href="/">
        <Button size="lg">Back to explore</Button>
      </Link>
    </main>
  );
}
