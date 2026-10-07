import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/Button";

export const metadata: Metadata = { title: "Airbnb your home" };

const STEPS = [
  ["Tell us about your place", "Share some basic info, like where it is and how many guests can stay."],
  ["Make it stand out", "Add 5 or more photos plus a title and description. We'll help you out."],
  ["Finish up and publish", "Choose a starting price, set your rules, and publish your listing."],
];

export default function HostHomesPage() {
  return (
    <main>
      <section className="bg-surface px-6 py-20 text-center">
        <h1 className="mx-auto max-w-[760px] text-[44px] font-bold leading-tight md:text-[64px]">Airbnb it.</h1>
        <p className="mx-auto mt-4 max-w-[560px] text-xl text-muted">
          Turn a spare room or a whole home into income. Hosting is free to start, and you decide your price, your rules and your calendar.
        </p>
        <Link href="/become-a-host/about" className="mt-8 inline-block">
          <Button size="lg">Get started</Button>
        </Link>
      </section>
      <section className="mx-auto max-w-[960px] px-6 py-16">
        <h2 className="mb-8 text-[32px] font-semibold">It&apos;s easy to get started on Airbnb</h2>
        <ol className="grid gap-8 md:grid-cols-3">
          {STEPS.map(([title, text], i) => (
            <li key={title} className="flex gap-4">
              <span className="text-2xl font-semibold">{i + 1}</span>
              <div>
                <h3 className="text-xl font-semibold">{title}</h3>
                <p className="mt-1 text-muted">{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
