import type { ServiceType } from "@/types/api";

/** Simple illustrated icons for the service tiles (drawn for this project). */
const ICONS: Record<ServiceType, React.ReactNode> = {
  photography: (
    <>
      <rect x="8" y="18" width="48" height="32" rx="6" fill="#4a5360" />
      <path d="M22 18l4-6h12l4 6z" fill="#7c8a99" />
      <circle cx="32" cy="34" r="11" fill="#2b3139" />
      <circle cx="32" cy="34" r="7" fill="#6f9fc4" />
      <circle cx="29.5" cy="31.5" r="2" fill="#fff" opacity=".7" />
      <rect x="46" y="22" width="5" height="3" rx="1" fill="#f3c653" />
    </>
  ),
  chefs: (
    <>
      <rect x="8" y="36" width="34" height="14" rx="3" fill="#b9854f" />
      <path d="M12 36c4-6 10-8 16-8s12 2 16 8z" fill="#e0833a" />
      <path d="M40 14l14 30-4 2-12-28z" fill="#cfd6dd" />
      <path d="M50 44l5-2 2 4-5 2z" fill="#4a3426" />
    </>
  ),
  training: (
    <>
      <circle cx="32" cy="38" r="15" fill="#3a3f47" />
      <circle cx="32" cy="38" r="8" fill="#51575f" />
      <path d="M22 26c0-8 4-12 10-12s10 4 10 12" stroke="#3a3f47" strokeWidth="5" fill="none" strokeLinecap="round" />
    </>
  ),
  makeup: (
    <>
      <rect x="14" y="14" width="10" height="26" rx="5" fill="#b99a7a" />
      <rect x="12" y="34" width="14" height="16" rx="3" fill="#3d4650" />
      <rect x="34" y="30" width="16" height="22" rx="3" fill="#2f3640" />
      <path d="M36 30V20a6 6 0 0 1 12 0v10z" fill="#d6455e" />
    </>
  ),
  hair: (
    <>
      <path d="M10 22c0-7 7-12 18-12h14c8 0 12 6 12 12s-4 10-12 10H28c-10 0-18-3-18-10z" fill="#6f9fc4" />
      <rect x="28" y="30" width="9" height="22" rx="4" fill="#3d4650" />
      <circle cx="46" cy="22" r="4" fill="#cfe3f1" />
    </>
  ),
  massage: (
    <>
      <ellipse cx="32" cy="46" rx="22" ry="7" fill="#c9c0b5" />
      <ellipse cx="24" cy="38" rx="12" ry="6" fill="#8f8780" />
      <ellipse cx="42" cy="30" rx="9" ry="5" fill="#a69e96" />
      <path d="M44 12c-3 4 2 6-1 10" stroke="#9ec9a0" strokeWidth="3" fill="none" strokeLinecap="round" />
    </>
  ),
};

export function ServiceIcon({ type, className = "" }: { type: ServiceType; className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      {ICONS[type]}
    </svg>
  );
}
