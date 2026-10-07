"use client";

import { CircleHelp, Globe, Menu, Moon, Sun, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { toast } from "@/components/ui/Toast";
import { setTheme, useTheme } from "@/lib/theme";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

const item = "flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors duration-150 hover:bg-surface";

function Line({ icon, children, onClick, bold }: { icon?: ReactNode; children: ReactNode; onClick: () => void; bold?: boolean }) {
  return (
    <button role="menuitem" className={`${item} ${bold ? "font-semibold" : ""}`} onClick={onClick}>
      {icon}
      {children}
    </button>
  );
}

function HostCard({ onClick }: { onClick: () => void }) {
  return (
    <button role="menuitem" onClick={onClick} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-surface">
      <span>
        <span className="block text-sm font-semibold">Become a host</span>
        <span className="block text-xs text-muted">It&apos;s easy to start hosting and earn extra income.</span>
      </span>
      <svg viewBox="0 0 40 40" className="size-10 shrink-0" aria-hidden>
        <path d="M6 20 20 7l14 13v13a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z" fill="#ffd9de" />
        <path d="M3 21 20 5l17 16-2.5 2.5L20 10 5.5 23.5z" fill="#ff385c" />
        <rect x="16" y="23" width="8" height="12" rx="1" fill="#ff385c" opacity=".35" />
      </svg>
    </button>
  );
}

/** "Become a host", the round account button and the round menu button, plus the dropdown they open. */
export function AccountControls() {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { user, status, logout } = useAuth();
  const openAuth = useUi((s) => s.openAuth);
  const theme = useTheme();

  useEffect(() => {
    if (!open) return;
    const outside = (event: MouseEvent) => !root.current?.contains(event.target as Node) && setOpen(false);
    const escape = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  const go = (path: string) => () => {
    setOpen(false);
    router.push(path);
  };
  const signIn = () => {
    setOpen(false);
    openAuth();
  };
  const authed = status === "authed" && user;
  const circle = "grid size-10 place-items-center rounded-full bg-chip text-ink transition-[background-color,box-shadow,transform] duration-200 ease-airbnb hover:bg-hover hover:shadow-pill active:scale-95";

  return (
    <div ref={root} className="relative flex items-center gap-1">
      <Link href="/host/homes" className="hidden rounded-full px-4 py-3 text-sm font-medium transition-colors duration-200 hover:bg-hover lg:block">
        Become a host
      </Link>
      <button onClick={() => setOpen((v) => !v)} aria-label="Account" className={circle}>
        {authed ? (
          <Avatar firstName={user.first_name} lastName={user.last_name} url={user.avatar_url} size={40} />
        ) : (
          <UserRound size={18} />
        )}
      </button>
      <button onClick={() => setOpen((v) => !v)} aria-haspopup="menu" aria-expanded={open} aria-label="Menu" className={circle}>
        <Menu size={18} />
      </button>

      {open && (
        <div role="menu" className="absolute right-0 top-12 z-50 w-[260px] origin-top-right animate-pop overflow-hidden rounded-[16px] bg-white py-2 text-ink shadow-modal">
          {authed ? (
            <>
              <Line bold onClick={go("/coming-soon/messages")}>Messages</Line>
              <Line bold onClick={go("/trips")}>Trips</Line>
              <Line bold onClick={go("/wishlists")}>Wishlists</Line>
              <hr className="my-2 border-line-soft" />
              {user.is_host ? (
                <Line onClick={go("/hosting")}>Manage listings</Line>
              ) : (
                <HostCard onClick={go("/host/homes")} />
              )}
              <Line onClick={go("/coming-soon/account")}>Account</Line>
              <hr className="my-2 border-line-soft" />
              <Line icon={<Globe size={16} />} onClick={go("/coming-soon/language")}>Languages &amp; currency</Line>
              <Line icon={<CircleHelp size={16} />} onClick={go("/help/home")}>Help Centre</Line>
              <Line
                icon={theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                {theme === "dark" ? "Light mode" : "Dark mode"}
              </Line>
              <hr className="my-2 border-line-soft" />
              <Line
                onClick={async () => {
                  setOpen(false);
                  await logout();
                  toast.success("You have been logged out");
                  router.push("/");
                }}
              >
                Log out
              </Line>
            </>
          ) : (
            <>
              <Line icon={<Globe size={16} />} onClick={go("/coming-soon/language")}>Languages &amp; currency</Line>
              <Line icon={<CircleHelp size={16} />} onClick={go("/help/home")}>Help Centre</Line>
              <Line
                icon={theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              >
                {theme === "dark" ? "Light mode" : "Dark mode"}
              </Line>
              <hr className="my-2 border-line-soft" />
              <HostCard onClick={go("/host/homes")} />
              <Line onClick={go("/refer")}>Refer a host</Line>
              <Line onClick={go("/host/co-hosts")}>Find a co-host</Line>
              <hr className="my-2 border-line-soft" />
              <Line onClick={signIn}>Log in or sign up</Line>
            </>
          )}
        </div>
      )}
    </div>
  );
}
