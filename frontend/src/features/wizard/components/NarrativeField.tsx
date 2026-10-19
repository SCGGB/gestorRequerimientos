import { useId } from "react";

import { Textarea } from "../../../components/ui/Textarea";

interface NarrativeFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
  required?: boolean;
  error?: string | null;
  hint?: string;
  disabled?: boolean;
  placeholder?: string;
}

export function NarrativeField({
  label,
  value,
  onChange,
  rows = 4,
  required,
  error,
  hint,
  disabled,
  placeholder,
}: NarrativeFieldProps) {
  const id = useId();

  return (
    <Textarea
      id={id}
      label={label}
      rows={rows}
      required={required}
      value={value}
      error={error}
      hint={hint}
      disabled={disabled}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
