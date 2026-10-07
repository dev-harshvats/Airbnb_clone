type AvatarProps = {
  firstName: string;
  lastName?: string;
  url?: string | null;
  size?: number;
  className?: string;
};

/** The user's photo, or their initials on a dark circle when there is none. */
export function Avatar({ firstName, lastName = "", url, size = 32, className = "" }: AvatarProps) {
  const style = { width: size, height: size, fontSize: size * 0.42 };
  if (url) {
    // eslint-disable-next-line @next/next/no-img-element -- small avatars; no optimisation needed
    return <img src={url} alt="" style={style} className={`shrink-0 rounded-full object-cover ${className}`} />;
  }
  return (
    <span
      style={style}
      className={`inline-grid shrink-0 place-items-center rounded-full bg-ink font-semibold text-white ${className}`}
    >
      {(firstName[0] ?? "") + (lastName[0] ?? "")}
    </span>
  );
}
