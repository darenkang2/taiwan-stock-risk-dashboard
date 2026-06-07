import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import type { UsReferenceResponse } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import { fmtNum } from "../lib/format";
import LightBadge from "./LightBadge";

interface Props {
  data: UsReferenceResponse;
}

// Phase 3：美股對照指標（國際對照，不併入台股綜合分數）
export default function UsReference({ data }: Props) {
  return (
    <section>
      <div className="mb-3 flex items-center gap-2">
        <h2 className="text-lg font-semibold text-ink">美股對照指標</h2>
        <span className="text-xs text-subtle">國際對照，不併入台股綜合分數</span>
        {data.is_mock && (
          <span className="rounded-full bg-canvas px-2 py-0.5 text-[11px] text-risk-yellow">
            mock（待接 ^VIX / CAPE / FRED）
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
        {data.indicators.map((ind) => {
          const color = LIGHT_COLOR[ind.light];
          return (
            <article key={ind.name} className="overflow-hidden rounded-2xl bg-white shadow-card">
              <div className="h-1 w-full" style={{ backgroundColor: color }} />
              <div className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-base font-semibold text-ink">{ind.name}</h3>
                  <LightBadge light={ind.light} size="sm" />
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-bold tabular-nums" style={{ color }}>
                    {fmtNum(ind.current, 2)}
                  </span>
                  {ind.unit && <span className="text-sm text-subtle">{ind.unit}</span>}
                </div>
                <div className="mt-0.5 text-xs text-subtle">歷史百分位 {fmtNum(ind.pctile, 0)}%</div>
                <div className="mt-3 h-16">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={ind.series} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
                      <YAxis hide domain={["auto", "auto"]} />
                      <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-subtle">{ind.hint}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
