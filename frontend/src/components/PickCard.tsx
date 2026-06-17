import type { StockPick, Style } from "../types";
import { LIGHT_COLOR } from "../lib/light";
import { STYLE_COLOR, STYLE_SHORT, STYLE_LABEL } from "../lib/style";
import { fmtNum } from "../lib/format";

interface Props {
  pick: StockPick;
  watched: boolean;
  onToggleWatch: (ticker: string) => void;
}

const STYLES: Style[] = ["value", "momentum", "dividend"];

function ScoreBar({ style, value, dominant }: { style: Style; value: number; dominant: boolean }) {
  const color = STYLE_COLOR[style];
  return (
    <div className="flex items-center gap-2">
      <span className="w-8 shrink-0 text-[11px] text-subtle">{STYLE_SHORT[style]}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full"
          style={{ width: `${value}%`, backgroundColor: color, opacity: dominant ? 1 : 0.45 }}
        />
      </div>
      <span className="w-7 shrink-0 text-right text-[11px] tabular-nums text-subtle">
        {Math.round(value)}
      </span>
    </div>
  );
}

export default function PickCard({ pick, watched, onToggleWatch }: Props) {
  const styleColor = STYLE_COLOR[pick.top_style];
  const riskColor = LIGHT_COLOR[pick.risk_light];
  const up = pick.change_pct >= 0;

  const metrics: { label: string; value: string }[] = [
    { label: "本益比", value: pick.per != null ? fmtNum(pick.per, 1) : "—" },
    { label: "殖利率", value: pick.dividend_yield != null ? `${fmtNum(pick.dividend_yield, 1)}%` : "—" },
    { label: "RSI", value: fmtNum(pick.rsi, 0) },
    { label: "年化波動", value: `${fmtNum(pick.vol_annual, 0)}%` },
    { label: "近3月", value: `${pick.ret_3m >= 0 ? "+" : ""}${fmtNum(pick.ret_3m, 1)}%` },
    { label: "距52週高", value: `-${fmtNum(pick.below_high_pct, 1)}%` },
  ];

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl bg-white shadow-card">
      <div className="h-1 w-full" style={{ backgroundColor: styleColor }} />
      <div className="flex flex-1 flex-col p-4">
        {/* 標題列 */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="truncate text-base font-semibold text-ink">{pick.name}</h3>
              <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-subtle">
                {pick.market === "tw" ? "台股" : "美股"} {pick.ticker}
              </span>
            </div>
            <div className="mt-0.5 flex items-baseline gap-2">
              <span className="text-lg font-semibold tabular-nums text-ink">
                {fmtNum(pick.price, 2)}
              </span>
              <span
                className="text-xs font-medium tabular-nums"
                style={{ color: up ? "#34C759" : "#FF3B30" }}
              >
                {up ? "+" : ""}
                {fmtNum(pick.change_pct, 2)}%
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onToggleWatch(pick.ticker)}
            title={watched ? "從追蹤清單移除" : "加入追蹤清單"}
            className="shrink-0 rounded-full p-1.5 text-lg leading-none transition hover:bg-gray-100"
            style={{ color: watched ? "#FF9F0A" : "#C7C7CC" }}
          >
            {watched ? "★" : "☆"}
          </button>
        </div>

        {/* 綜合分數 + 主導風格 + 風險燈 */}
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-bold tracking-tight" style={{ color: styleColor }}>
              {fmtNum(pick.score, 1)}
            </span>
            <span className="text-[11px] text-subtle">/ 100 選股分</span>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span
              className="rounded-full px-2 py-0.5 text-[11px] font-medium"
              style={{ backgroundColor: `${styleColor}1A`, color: styleColor }}
            >
              {STYLE_LABEL[pick.top_style]}
            </span>
            <span className="flex items-center gap-1 text-[11px]" style={{ color: riskColor }}>
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: riskColor }}
              />
              風險{pick.risk_light === "red" ? "高" : pick.risk_light === "yellow" ? "中" : "低"}
            </span>
          </div>
        </div>

        {/* 三風格子分數 */}
        <div className="mt-3 space-y-1.5">
          {STYLES.map((s) => (
            <ScoreBar key={s} style={s} value={pick.scores[s]} dominant={s === pick.top_style} />
          ))}
        </div>

        {/* 標籤 */}
        {pick.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {pick.tags.map((t) => (
              <span
                key={t}
                className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-ink"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {/* 指標 */}
        <dl className="mt-3 grid grid-cols-3 gap-x-3 gap-y-2 border-t border-gray-100 pt-3">
          {metrics.map((m) => (
            <div key={m.label} className="flex flex-col">
              <dt className="text-[10px] text-subtle">{m.label}</dt>
              <dd className="text-sm font-medium tabular-nums text-ink">{m.value}</dd>
            </div>
          ))}
        </dl>

        <p className="mt-3 text-[11px] leading-relaxed text-subtle">{pick.rationale}</p>
      </div>
    </article>
  );
}
