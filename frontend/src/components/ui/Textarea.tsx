import { useId } from "react";
import type { TextareaHTMLAttributes } from "react";

interface TextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> {
  id?: string;
  label?: string;
  error?: string | null;
  hint?: string;
}

const baseFieldClasses =
  "w-full rounded border bg-surface px-3 py-2 text-sm text-secondary placeholder:text-outline focus:outline-none focus:ring-[3px] focus:ring-primary/25";

export function Textarea({
  id,
  label,
  error,
  hint,
  required,
  rows = 4,
  className = "",
  ...rest
}: TextareaProps) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;
  const messageId = `${textareaId}-message`;

  return (
    <div className="flex flex-col gap-1">
      {label !== undefined && (
        <label htmlFor={textareaId} className="text-sm font-semibold text-neutral-dark">
          {label}
          {required === true && <span className="ml-1 text-danger">*</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
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
