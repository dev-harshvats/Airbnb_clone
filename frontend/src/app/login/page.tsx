"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useUi } from "@/store/ui";

/** /login opens the login dialog over the home page, as the original does. */
export default function LoginPage() {
  const router = useRouter();
  useEffect(() => {
    useUi.getState().openAuth({ redirectTo: "/", onCancel: () => router.replace("/") });
    router.replace("/");
  }, [router]);
  return null;
}
