import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { Wizard } from "@/components/host/Wizard";
import { WIZARD_STEPS, type StepKey } from "@/lib/hosting";

export const metadata: Metadata = { title: "Airbnb your home" };

export default async function Page({ params }: { params: Promise<{ step: string }> }) {
  const { step } = await params;
  if (!(WIZARD_STEPS as readonly string[]).includes(step)) notFound();
  return (
    <RequireAuth>
      <Wizard step={step as StepKey} />
    </RequireAuth>
  );
}
