import { Minus, Plus } from "lucide-react";

type StepperProps = {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label: string;
};

/** A round − / + control around a number, used for guests and room counts. */
export function Stepper({ value, onChange, min = 0, max = 99, step = 1, label }: StepperProps) {
  const button = "grid size-8 place-items-center rounded-full border border-muted text-muted transition enabled:hover:border-ink enabled:hover:text-ink disabled:cursor-not-allowed disabled:opacity-30";
  return (
    <div className="flex items-center gap-4">
      <button type="button" aria-label={`Decrease ${label}`} disabled={value - step < min} onClick={() => onChange(value - step)} className={button}>
        <Minus size={14} />
      </button>
      <span className="w-5 text-center text-base" aria-live="polite">{value}</span>
      <button type="button" aria-label={`Increase ${label}`} disabled={value + step > max} onClick={() => onChange(value + step)} className={button}>
        <Plus size={14} />
      </button>
    </div>
  );
}
