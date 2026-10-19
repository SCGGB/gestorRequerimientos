import { Badge } from "./Badge";
import type { BadgeTone } from "./Badge";

interface StatusBadgeProps {
  label: string;
  tone: BadgeTone;
}

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return <Badge label={label} tone={tone} />;
}
