import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Composite } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import { fmtShortDate } from "../lib/format";

const CX = 100;
const CY = 100;
const R = 80;

function polar(value: number, radius = R): [number, number] {
  // value 0–100 → 角度 180°(左) → 0°(右)
  const theta = (Math.PI * (100 - value)) / 100;
  return [CX + radius * Math.cos(theta), CY - radius * Math.sin(theta)];
}

function arc(from: number, to: number): string {
  const [x1, y1] = polar(from);
  const [x2, y2] = polar(to);
  return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`;
}

interface Props {
  composite: Composite;
}

export default function RiskGauge({ composite }: Props) {
  const color = LIGHT_COLOR[composite.light];
  const [nx, ny] = polar(composite.score, R - 14);

  return (
    <section className="rounded-2xl bg-white p-6 shadow-card sm:p-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ink">綜合風險溫度計</h2>
        <span className="text-xs text-subtle">0–40 風險低 · 40–70 留意 · 70–100 高風險</span>
      </div>

      <div className="mt-2 flex flex-col items-center gap-6 lg:flex-row lg:items-center lg:gap-10">
        {/* 半圓儀表 */}
        <div className="relative w-full max-w-[320px]">
          <svg viewBox="0 0 200 116" className="w-full">
            <path d={arc(0, 100)} fill="none" stroke="#E8E8ED" strokeWidth={16} strokeLinecap="round" />
            <path d={arc(0, 40)} fill="none" stroke={LIGHT_COLOR.green} strokeWidth={16} strokeLinecap="round" />
            <path d={arc(40, 70)} fill="none" stroke={LIGHT_COLOR.yellow} strokeWidth={16} />
            <path d={arc(70, 100)} fill="none" stroke={LIGHT_COLOR.red} strokeWidth={16} strokeLinecap="round" />
            {/* 指針 */}
            <line x1={CX} y1={CY} x2={nx} y2={ny} stroke={color} strokeWidth={3} strokeLinecap="round" />
            <circle cx={CX} cy={CY} r={6} fill={color} />
          </svg>
          <div className="-mt-10 text-center">
            <div className="text-5xl font-bold tracking-tight" style={{ color }}>
              {composite.score}
            </div>
            <div className="mt-1 text-base font-medium" style={{ color }}>
              {composite.label}
            </div>
          </div>
        </div>

        {/* 觀測提示 + 趨勢 */}
        <div className="w-full flex-1">
          <div
            className="rounded-xl p-4 text-sm leading-relaxed text-ink"
            style={{ backgroundColor: `${color}14` }}
          >
            {composite.hint}
          </div>
          <div className="mt-4">
            <div className="mb-1 text-xs text-subtle">近 90 日風險分數趨勢</div>
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={composite.trend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gaugeTrend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={color} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="date"
                    tickFormatter={fmtShortDate}
                    tick={{ fontSize: 10, fill: "#86868B" }}
                    interval="preserveStartEnd"
                    minTickGap={40}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 10, fill: "#86868B" }}
                    axisLine={false}
                    tickLine={false}
                    width={32}
                  />
                  <Tooltip
                    formatter={(v: number) => [`${v}`, "風險分數"]}
                    labelFormatter={fmtShortDate}
                    contentStyle={{ borderRadius: 12, border: "none", boxShadow: "0 4px 16px rgba(0,0,0,0.1)", fontSize: 12 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke={color}
                    strokeWidth={2}
                    fill="url(#gaugeTrend)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
