/** A shimmering placeholder block; size it with className (for example "h-4 w-32"). */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`animate-shimmer rounded-control bg-surface ${className}`} />;
}
