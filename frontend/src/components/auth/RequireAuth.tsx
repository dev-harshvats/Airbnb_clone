"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Skeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

/**
 * Wrap a page that needs a logged-in user. Visitors get the login dialog; after logging in they
 * stay on (or return to) this page, and if they dismiss it they are sent back to the home page.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const status = useAuth((s) => s.status);
  const openAuth = useUi((s) => s.openAuth);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (status === "anon") openAuth({ redirectTo: pathname, onCancel: () => router.replace("/") });
  }, [status, pathname, openAuth, router]);

  if (status !== "authed") {
    return (
      <div className="mx-auto max-w-[1120px] space-y-4 px-6 py-10">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  return <>{children}</>;
}
