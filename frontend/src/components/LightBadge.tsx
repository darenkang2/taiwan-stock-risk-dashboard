import type { Light } from "../types";
import { LIGHT_COLOR, LIGHT_LABEL } from "../lib/light";

interface Props {
  light: Light;
  size?: "sm" | "md";
}

export default function LightBadge({ light, size = "md" }: Props) {
  const dot = size === "sm" ? 10 : 14;
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium"
      style={{ backgroundColor: `${LIGHT_COLOR[light]}1A`, color: LIGHT_COLOR[light] }}
    >
      <span
        className="inline-block rounded-full"
        style={{ width: dot, height: dot, backgroundColor: LIGHT_COLOR[light] }}
      />
      {LIGHT_LABEL[light]}
    </span>
  );
}
