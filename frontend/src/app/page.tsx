import { Logo } from "@/components/ui/Logo";

/** Placeholder explore page; the real grid arrives with the explore feature. */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <Logo />
      <p className="text-muted">Find your next stay across India.</p>
    </main>
  );
}
