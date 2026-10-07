/** Small illustrated icons for the Homes / Experiences / Services tabs (drawn for this project). */

export function GlobeIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <g className="tab-icon tab-icon-globe">
        <circle cx="24" cy="24" r="17" fill="#6ec1c9" />
        <path d="M12 18c5-2 7 2 11 1 3-1 3-5 8-5 3 0 5 2 7 5-1 4-5 3-6 7-1 3 1 6-2 9-6 3-14 1-18-4-3-4-3-10 0-13z" fill="#f3c653" />
        <path d="M18 9c3 1 4 3 8 3" stroke="#fff" strokeWidth="2" strokeLinecap="round" fill="none" opacity=".7" />
      </g>
      <rect x="19" y="39" width="10" height="4" rx="2" fill="#8b5a3c" />
    </svg>
  );
}

export function HouseIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <g className="tab-icon tab-icon-house">
        <path d="M7 24 24 9l17 15v15a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2z" fill="#d9a066" />
        <path d="M4 25 24 7l20 18-3 3L24 13 7 28z" fill="#c8453d" />
        <rect x="21" y="28" width="7" height="13" fill="#3a2414" />
        <rect x="20" y="28" width="9" height="13" rx="1" fill="#7a4a2b" className="tab-icon-door" />
        <rect x="10" y="27" width="7" height="7" rx="1" fill="#bfe3ec" />
        <rect x="32" y="27" width="6" height="7" rx="1" fill="#bfe3ec" />
      </g>
    </svg>
  );
}

export function BalloonIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <g className="tab-icon tab-icon-balloon">
        <path d="M24 4c8 0 13 6 13 13 0 6-5 11-9 15h-8c-4-4-9-9-9-15C11 10 16 4 24 4z" fill="#e0453b" />
        <path d="M24 4c-4 4-6 9-6 14s2 10 5 14h2c3-4 5-9 5-14S28 8 24 4z" fill="#f3c653" />
        <path d="M20 32h8l-1 5h-6z" fill="#8b5a3c" />
        <rect x="19" y="37" width="10" height="6" rx="1.5" fill="#a9703f" />
      </g>
    </svg>
  );
}

export function BellIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden>
      <path d="M6 36h36v4H6z" fill="#7c8a99" />
      <g className="tab-icon tab-icon-bell">
        <path d="M10 36c0-9 6-16 14-16s14 7 14 16z" fill="#4a5360" />
        <path d="M14 34c1-6 5-11 10-12" stroke="#fff" strokeWidth="2" strokeLinecap="round" fill="none" opacity=".4" />
        <circle cx="24" cy="17" r="3" fill="#f3c653" />
        <rect x="22.5" y="18" width="3" height="3" fill="#f3c653" />
      </g>
    </svg>
  );
}
