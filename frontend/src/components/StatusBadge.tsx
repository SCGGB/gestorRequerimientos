interface StatusBadgeProps {
  label: string;
  tone: "success" | "warning" | "danger" | "neutral";
}

const toneClasses: Record<StatusBadgeProps["tone"], string> = {
  success: "bg-success/10 text-success border-success/40",
  warning: "bg-warning/10 text-warning border-warning/40",
  danger: "bg-danger/10 text-danger border-danger/40",
  neutral: "bg-muted text-neutral-dark border-border",
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.05em] ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}