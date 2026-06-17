import {
  Area,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MarginPoint, PerPoint, VixPoint } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import { fmtShortDate } from "../lib/format";

const axisX = {
  dataKey: "date",
  tickFormatter: fmtShortDate,
  tick: { fontSize: 10, fill: "#86868B" },
  interval: "preserveStartEnd" as const,
  minTickGap: 40,
  axisLine: false,
  tickLine: false,
};

const tooltipStyle = {
  borderRadius: 12,
  border: "none",
  boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
  fontSize: 12,
};

// 前兆1：融資餘額 vs 法人累計買賣超（雙軸）
export function MarginChart({ data }: { data: MarginPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 6, right: 4, left: -8, bottom: 0 }}>
        <XAxis {...axisX} />
        <YAxis yAxisId="m" tick={{ fontSize: 10, fill: "#86868B" }} axisLine={false} tickLine={false} width={42} />
        <YAxis yAxisId="i" orientation="right" tick={{ fontSize: 10, fill: "#86868B" }} axisLine={false} tickLine={false} width={42} />
        <Tooltip
          labelFormatter={fmtShortDate}
          formatter={(v: number, n: string) => [v, n === "margin" ? "融資餘額" : "法人累計買賣超"]}
          contentStyle={tooltipStyle}
        />
        <ReferenceLine yAxisId="i" y={0} stroke="#D2D2D7" strokeDasharray="3 3" />
        <Line yAxisId="m" type="monotone" dataKey="margin" name="margin" stroke="#0A84FF" strokeWidth={2} dot={false} />
        <Line yAxisId="i" type="monotone" dataKey="inst_cum" name="inst_cum" stroke={LIGHT_COLOR.red} strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// 前兆2：本益比走勢 + 均值線 + ±1σ/±2σ 帶狀
export function PerChart({ data }: { data: PerPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="perBand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FF9F0A" stopOpacity={0.12} />
            <stop offset="100%" stopColor="#FF9F0A" stopOpacity={0.12} />
          </linearGradient>
        </defs>
        <XAxis {...axisX} />
        <YAxis tick={{ fontSize: 10, fill: "#86868B" }} axisLine={false} tickLine={false} width={36} domain={["auto", "auto"]} />
        <Tooltip
          labelFormatter={fmtShortDate}
          formatter={(v: number, n: string) => {
            const map: Record<string, string> = { per: "本益比", mean: "均值", upper1: "+1σ", upper2: "+2σ" };
            return [v, map[n] ?? n];
          }}
          contentStyle={tooltipStyle}
        />
        {/* ±2σ 帶狀（以兩條線界定，視覺以淡黃標示高檔區） */}
        <ReferenceLine y={data[0]?.upper1} stroke="#FF9F0A" strokeDasharray="4 4" />
        <ReferenceLine y={data[0]?.upper2} stroke={LIGHT_COLOR.red} strokeDasharray="4 4" />
        <Line type="monotone" dataKey="mean" name="mean" stroke="#86868B" strokeWidth={1} dot={false} strokeDasharray="2 2" />
        <Line type="monotone" dataKey="per" name="per" stroke="#1D1D1F" strokeWidth={2} dot={false} />
        <Area type="monotone" dataKey="upper2" stroke="none" fill="url(#perBand)" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// 前兆3：波動率走勢 + 歷史低檔分位線（低＝高風險）
export function VixChart({ data }: { data: VixPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
        <XAxis {...axisX} />
        <YAxis tick={{ fontSize: 10, fill: "#86868B" }} axisLine={false} tickLine={false} width={36} domain={["auto", "auto"]} />
        <Tooltip
          labelFormatter={fmtShortDate}
          formatter={(v: number, n: string) => {
            const map: Record<string, string> = { vix: "波動率", p10: "最低10%線", p25: "最低25%線" };
            return [v, map[n] ?? n];
          }}
          contentStyle={tooltipStyle}
        />
        <ReferenceLine y={data[0]?.p25} stroke="#FF9F0A" strokeDasharray="4 4" />
        <ReferenceLine y={data[0]?.p10} stroke={LIGHT_COLOR.red} strokeDasharray="4 4" />
        <Line type="monotone" dataKey="vix" name="vix" stroke="#5856D6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
