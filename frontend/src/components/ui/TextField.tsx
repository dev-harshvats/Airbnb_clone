import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  /** Something shown at the right edge of the field (for example a "Show" toggle). */
  trailing?: ReactNode;
};

/** Airbnb-style field: a bordered box with a small label above the value. */
export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, trailing, className = "", id, ...rest },
  ref,
) {
  const generated = useId();
  const inputId = id ?? generated;
  return (
    <div className={className}>
      <div
        className={`flex items-center rounded-control border bg-white px-3 transition focus-within:border-ink focus-within:ring-1 focus-within:ring-ink
          ${error ? "border-[#c13515] bg-[#fff8f6]" : "border-muted"}`}
      >
        <label htmlFor={inputId} className="block flex-1 py-2">
          <span className="block text-xs text-muted">{label}</span>
          <input
            ref={ref}
            id={inputId}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
            className="w-full bg-transparent text-base outline-none"
            {...rest}
          />
        </label>
        {trailing}
      </div>
      {error && (
        <p id={`${inputId}-error`} role="alert" className="mt-1.5 text-xs text-[#c13515]">
          {error}
        </p>
      )}
    </div>
  );
});
