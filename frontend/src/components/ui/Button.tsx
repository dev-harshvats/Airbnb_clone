import { forwardRef, type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "dark" | "secondary" | "ghost" | "link";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-rausch-gradient text-white hover:brightness-95 active:scale-[0.98]",
  dark: "bg-ink text-white hover:bg-black active:scale-[0.98]",
  secondary: "border border-ink bg-white text-ink hover:bg-surface active:scale-[0.98]",
  ghost: "text-ink hover:bg-surface",
  link: "text-ink underline underline-offset-2 hover:text-black",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  /** Shows a spinner and blocks clicks while an action is in flight. */
  loading?: boolean;
  fullWidth?: boolean;
};

/** Forwards every native button prop and ref, so it can replace a plain <button> anywhere. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading, fullWidth, className = "", disabled, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-control font-semibold transition
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink
        disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${SIZES[size]}
        ${fullWidth ? "w-full" : ""} ${className}`}
      {...rest}
    >
      {loading && (
        <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
});
