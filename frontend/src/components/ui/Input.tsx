import { useId } from "react";
import type { InputHTMLAttributes } from "react";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  id?: string;
  label?: string;
  error?: string | null;
  hint?: string;
}

const baseFieldClasses =
  "h-10 w-full rounded border bg-surface px-3 text-sm text-secondary placeholder:text-outline focus:outline-none focus:ring-[3px] focus:ring-primary/25";

export function Input({
  id,
  label,
  error,
  hint,
  required,
  className = "",
  ...rest
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const messageId = `${inputId}-message`;

  return (
    <div className="flex flex-col gap-1">
      {label !== undefined && (
        <label htmlFor={inputId} className="text-sm font-semibold text-neutral-dark">
          {label}
          {required === true && <span className="ml-1 text-danger">*</span>}
        </label>
      )}
      <input
        id={inputId}
        required={required}
        aria-invalid={error != null ? true : undefined}
        aria-describedby={error != null || hint !== undefined ? messageId : undefined}
        className={`${baseFieldClasses} ${error != null ? "border-danger" : "border-outline-variant focus:border-primary"} ${className}`}
        {...rest}
      />
      {error != null ? (
        <p id={messageId} className="text-xs text-danger">
          {error}
        </p>
      ) : hint !== undefined ? (
        <p id={messageId} className="text-xs text-neutral-dark">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
