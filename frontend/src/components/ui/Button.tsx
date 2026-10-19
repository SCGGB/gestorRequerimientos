import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-primary bg-primary text-on-primary hover:bg-primary-hover focus-visible:ring-primary/25",
  secondary:
    "border-outline-variant bg-transparent text-secondary hover:bg-muted focus-visible:ring-primary/25",
  danger:
    "border-danger bg-danger text-on-primary hover:bg-danger-hover focus-visible:ring-danger/25",
  ghost:
    "border-transparent bg-transparent text-neutral-dark hover:bg-muted focus-visible:ring-primary/25",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  variant = "primary",
  size = "md",
  type = "button",
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded border font-semibold transition-colors focus-visible:outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...rest}
    />
  );
}
