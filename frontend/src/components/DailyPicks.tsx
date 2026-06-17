import { useMemo, useState } from "react";
import type { PicksResponse } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import { STYLE_COLOR, STYLE_LABEL } from "../lib/style";
import PickCard from "./PickCard";

interface Props {
  data: PicksResponse;
  watch: string[];
  onToggleWatch: (ticker: string) => void;
}

type MarketFilter = "all" | "tw" | "us";

const MARKET_TABS: { key: MarketFilter; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "tw", label: "台股" },
  { key: "us", label: "美股" },
];

export default function DailyPicks({ data, watch, onToggleWatch }: Props) {
  const [market, setMarket] = useState<MarketFilter>("all");
  const watchSet = useMemo(() => new Set(watch), [watch]);

  const top = market === "all" ? data.top : data.top.filter((p) => p.market === market);
  const warnings =
    market === "all" ? data.warnings : data.warnings.filter((p) => p.market === market);

  const riskColor = LIGHT_COLOR[data.market_risk_light];
  const riskWord =
    data.market_risk_light === "red"
      ? "高風險"
      : data.market_risk_light === "yellow"
        ? "留意"
        : "風險低";

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">每日選股</h2>
          <p className="mt-1 text-xs leading-relaxed text-subtle">
            掃描大型權值股（台股 0050/0100＋美股 Nasdaq100/S&P500），融合「價值・動能・存股」三風格評分。
            僅為符合策略條件之<strong className="text-ink">觀察名單</strong>，非買賣建議。
          </p>
        </div>
        {/* 市場篩選 */}
        <div className="flex rounded-full bg-gray-100 p-0.5">
          {MARKET_TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setMarket(t.key)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                market === t.key ? "bg-white text-ink shadow-sm" : "text-subtle"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* 大盤燈 + 風格權重 */}
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-2xl bg-white px-4 py-3 shadow-card">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-subtle">大盤頂部風險</span>
          <span className="flex items-center gap-1.5 font-medium" style={{ color: riskColor }}>
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: riskColor }} />
            {riskWord}
          </span>
          {data.market_risk_light === "red" && (
            <span className="text-xs text-subtle">— 整體偏高，候選標的請更留意系統性風險</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-subtle">
          <span>風格權重</span>
          {(["value", "momentum", "dividend"] as const).map((s) => (
            <span key={s} className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: STYLE_COLOR[s] }} />
              {STYLE_LABEL[s]} {Math.round(data.style_weights[s] * 100)}%
            </span>
          ))}
        </div>
      </div>

      {/* 每日精選候選 */}
      <h3 className="mb-3 mt-6 text-sm font-semibold text-ink">
        每日精選候選 <span className="font-normal text-subtle">（分數前段 {top.length} 檔）</span>
      </h3>
      {top.length === 0 ? (
        <p className="text-sm text-subtle">此市場目前無符合條件的精選標的。</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {top.map((p) => (
            <PickCard key={p.ticker} pick={p} watched={watchSet.has(p.ticker)} onToggleWatch={onToggleWatch} />
          ))}
        </div>
      )}

      {/* 風險警示 */}
      {warnings.length > 0 && (
        <>
          <h3 className="mb-3 mt-8 text-sm font-semibold text-ink">
            風險警示 <span className="font-normal text-subtle">（過熱／偏貴 {warnings.length} 檔，宜避追高）</span>
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {warnings.map((p) => (
              <PickCard key={p.ticker} pick={p} watched={watchSet.has(p.ticker)} onToggleWatch={onToggleWatch} />
            ))}
          </div>
        </>
      )}

      <p className="mt-4 text-[11px] leading-relaxed text-subtle">{data.disclaimer}</p>
    </section>
  );
}
