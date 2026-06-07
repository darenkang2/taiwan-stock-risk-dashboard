import { useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BacktestResponse } from "../types";
import { fetchBacktest } from "../api";
import { LIGHT_COLOR } from "../lib/light";
import { fmtNum } from "../lib/format";

interface Props {
  initial: BacktestResponse;
}

const HORIZONS = [10, 20, 60];

export default function Backtest({ initial }: Props) {
  const [data, setData] = useState<BacktestResponse>(initial);
  const [loading, setLoading] = useState(false);

  async function changeHorizon(h: number) {
    if (h === data.horizon) return;
    setLoading(true);
    setData(await fetchBacktest(h));
    setLoading(false);
  }

  const chartData = data.buckets.map((b) => ({
    name: b.label,
    value: b.avg_forward_return,
    light: b.light,
    count: b.count,
  }));

  return (
    <section className="rounded-2xl bg-white p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">風險分數歷史回測</h2>
          <p className="mt-0.5 text-xs text-subtle">
            對照各風險區間「{data.horizon} 日後加權指數平均報酬」，檢視高風險是否對應較弱後續走勢。
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-full bg-canvas p-1">
          {HORIZONS.map((h) => (
            <button
              key={h}
              onClick={() => changeHorizon(h)}
              className={`rounded-full px-3 py-1 text-sm transition ${
                h === data.horizon ? "bg-white font-medium text-ink shadow-sm" : "text-subtle"
              }`}
            >
              {h} 日
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_240px]">
        <div className={`h-56 transition-opacity ${loading ? "opacity-40" : ""}`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 16, right: 8, left: -16, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#86868B" }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 10, fill: "#86868B" }}
                axisLine={false}
                tickLine={false}
                unit="%"
              />
              <Tooltip
                formatter={(v: number, _n, p) => [`${fmtNum(v, 2)}%（樣本 ${p.payload.count}）`, "平均後續報酬"]}
                contentStyle={{ borderRadius: 12, border: "none", boxShadow: "0 4px 16px rgba(0,0,0,0.1)", fontSize: 12 }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                <LabelList dataKey="value" position="top" formatter={(v: number) => `${fmtNum(v, 1)}%`} style={{ fontSize: 12, fill: "#1D1D1F" }} />
                {chartData.map((d) => (
                  <Cell key={d.light} fill={LIGHT_COLOR[d.light]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="flex flex-col justify-center gap-4">
          <div className="rounded-xl bg-canvas p-4">
            <div className="text-xs text-subtle">風險分數 vs 後續報酬 相關係數</div>
            <div
              className="mt-1 text-3xl font-bold tabular-nums"
              style={{ color: data.correlation < 0 ? LIGHT_COLOR.green : LIGHT_COLOR.red }}
            >
              {data.correlation > 0 ? "+" : ""}
              {fmtNum(data.correlation, 2)}
            </div>
            <div className="mt-1 text-[11px] leading-relaxed text-subtle">
              負值代表「風險分數越高、後續報酬越弱」，方向符合防禦框架的假設。
            </div>
          </div>
          <div className="text-[11px] leading-relaxed text-subtle">
            樣本數：{data.points.length} 個交易日。
            {data.is_mock && " 目前為 mock 資料，僅示範回測方法；"}
            歷史關聯不代表未來必然發生。
          </div>
        </div>
      </div>
    </section>
  );
}
