import {
  AlarmSmoke, Bath, BellRing, Car, Check, Coffee, CookingPot, Dumbbell, FireExtinguisher, Flame, Flower2,
  HeartPulse, Laptop, Mountain, Shirt, ShowerHead, Snowflake, Sun, Tv, Umbrella, Utensils, WashingMachine,
  Waves, Wifi, Wind, type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  wifi: Wifi, kitchen: CookingPot, washer: WashingMachine, ac: Snowflake, heating: Flame, tv: Tv,
  hot_water: ShowerHead, hair_dryer: Wind, iron: Shirt, workspace: Laptop, breakfast: Coffee,
  pool: Waves, hot_tub: Bath, parking: Car, gym: Dumbbell, bbq: Utensils, balcony: Sun, bonfire: Flame,
  garden: Flower2, beach: Umbrella, lake: Waves, sea_view: Waves, mountain: Mountain,
  smoke_alarm: BellRing, first_aid: HeartPulse, extinguisher: FireExtinguisher, co_alarm: AlarmSmoke,
};

/** The icon for an amenity's `icon_key`; unknown keys get a tick. */
export function AmenityIcon({ iconKey, size = 24 }: { iconKey: string; size?: number }) {
  const Icon = ICONS[iconKey] ?? Check;
  return <Icon size={size} strokeWidth={1.5} aria-hidden />;
}
