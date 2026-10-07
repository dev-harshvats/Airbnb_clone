const rupees = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

/** 12500 -> "₹12,500"; Indian digit grouping (1250000 -> "₹12,50,000"). */
export function formatINR(amount: number): string {
  return `₹${rupees.format(amount)}`;
}

/** Calendar dates ("2026-10-12") are plain dates, so everything is formatted in UTC. */
function parts(isoDate: string) {
  const date = new Date(`${isoDate}T00:00:00Z`);
  const format = (options: Intl.DateTimeFormatOptions) =>
    new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", ...options }).format(date);
  return {
    day: format({ day: "numeric" }),
    month: format({ month: "short" }),
    year: format({ year: "numeric" }),
  };
}

/** "12–17 Oct", "28 Oct – 2 Nov", or with years when the stay crosses a year boundary. */
export function formatRange(checkIn: string, checkOut: string): string {
  const a = parts(checkIn);
  const b = parts(checkOut);
  if (a.year !== b.year) return `${a.day} ${a.month} ${a.year} – ${b.day} ${b.month} ${b.year}`;
  if (a.month !== b.month) return `${a.day} ${a.month} – ${b.day} ${b.month}`;
  return `${a.day}–${b.day} ${a.month}`;
}

/** Number of nights between two calendar dates ("2026-10-12", "2026-10-17" -> 5). */
export function nightsBetween(checkIn: string, checkOut: string): number {
  const day = 24 * 60 * 60 * 1000;
  return Math.round((Date.parse(`${checkOut}T00:00:00Z`) - Date.parse(`${checkIn}T00:00:00Z`)) / day);
}

/** "08:30" -> "8:30 am", "19:00" -> "7:00 pm". */
export function formatTime(hhmm: string): string {
  const [hours, minutes] = hhmm.split(":").map(Number);
  const suffix = hours >= 12 ? "pm" : "am";
  return `${hours % 12 || 12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

/** 150 -> "2.5 hours", 90 -> "1.5 hours", 60 -> "1 hour". */
export function formatDuration(minutes: number): string {
  const hours = minutes / 60;
  return `${Number.isInteger(hours) ? hours : hours.toFixed(1)} ${hours === 1 ? "hour" : "hours"}`;
}
