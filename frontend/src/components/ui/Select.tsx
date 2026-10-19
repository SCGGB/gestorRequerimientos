import { useId } from "react";
import type { SelectHTMLAttributes } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "id" | "children"> {
  id?: string;
  label?: string;
  error?: string | null;
  hint?: string;
  options: SelectOption[];
  placeholder?: string;
}

export function Select({
  id,
  label,
  error,
  hint,
  options,
  placeholder,
  required,
  className = "",
  ...rest
}: SelectProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const messageId = `${selectId}-message`;

  return (
    <div className="flex flex-col gap-1">
      {label !== undefined && (
        <label htmlFor={selectId} className="text-sm font-semibold text-neutral-dark">
          {label}
          {required === true && <span className="ml-1 text-danger">*</span>}
        </label>
      )}
      <select
        id={selectId}
        required={required}
        aria-invalid={error != null ? true : undefined}
        aria-describedby={error != null || hint !== undefined ? messageId : undefined}
        className={`h-10 w-full rounded border bg-surface px-3 text-sm text-secondary focus:outline-none focus:ring-[3px] focus:ring-primary/25 ${error != null ? "border-danger" : "border-outline-variant focus:border-primary"} ${className}`}
        {...rest}
      >
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
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
