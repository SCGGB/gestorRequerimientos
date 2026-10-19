interface FieldErrorProps {
  message: string;
  id?: string;
}

export function FieldError({ message, id }: FieldErrorProps) {
  return (
    <p
      id={id}
      aria-live="polite"
      className="text-xs text-danger"
    >
      {message}
    </p>
  );
}
