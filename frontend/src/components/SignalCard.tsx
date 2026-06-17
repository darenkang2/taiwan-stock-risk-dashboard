import type { ReactNode } from "react";
import type { Light } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import LightBadge from "./LightBadge";

interface Metric {
  label: string;
  value: string;
  emphasis?: boolean;
}

interface Props {
  index: number;
  title: string;
  subtitle: string;
  light: Light;
  score: number;
  metrics: Metric[];
  note?: string;
  children: ReactNode; // 圖表
}

export default function SignalCard({
  index,
  title,
  subtitle,
  light,
  score,
  metrics,
  note,
  children,
}: Props) {
  const color = LIGHT_COLOR[light];
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl bg-white shadow-card">
      <div className="h-1 w-full" style={{ backgroundColor: color }} />
      <div className="flex flex-1 flex-col p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs font-medium text-subtle">前兆 {index}</div>
            <h3 className="mt-0.5 text-base font-semibold text-ink">{title}</h3>
            <p className="mt-1 text-xs leading-relaxed text-subtle">{subtitle}</p>
          </div>
          <LightBadge light={light} size="sm" />
        </div>

        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight" style={{ color }}>
            {score}
          </span>
          <span className="text-xs text-subtle">/ 100 子分數</span>
        </div>

        <div className="mt-4 h-36">{children}</div>

        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 border-t border-gray-100 pt-3">
          {metrics.map((m) => (
            <div key={m.label} className="flex items-center justify-between">
              <dt className="text-xs text-subtle">{m.label}</dt>
              <dd
                className="text-sm font-medium tabular-nums"
                style={{ color: m.emphasis ? color : "#1D1D1F" }}
              >
                {m.value}
              </dd>
            </div>
          ))}
        </dl>

        {note && <p className="mt-3 text-[11px] leading-relaxed text-subtle">{note}</p>}
      </div>
    </article>
  );
}
