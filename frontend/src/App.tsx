import { useEffect, useState } from "react";
import {
  fetchRisk,
  refreshRisk,
  fetchUsReference,
  fetchBacktest,
  fetchPicks,
  type RiskResult,
} from "./api";
import { fetchConfig, DEFAULT_CONFIG, type PlatformConfig } from "./lib/config";
import type { BacktestResponse, PicksResponse, UsReferenceResponse } from "./types";
import Header from "./components/Header";
import RiskGauge from "./components/RiskGauge";
import SignalCard from "./components/SignalCard";
import { MarginChart, PerChart, VixChart } from "./components/SignalCharts";
import ModuleC from "./components/ModuleC";
import ModuleD from "./components/ModuleD";
import UsReference from "./components/UsReference";
import Backtest from "./components/Backtest";
import DailyPicks from "./components/DailyPicks";
import Watchlist from "./components/Watchlist";
import { useLocalStorage } from "./lib/useLocalStorage";
import { fmtNum } from "./lib/format";

export default function App() {
  const [result, setResult] = useState<RiskResult | null>(null);
  const [config, setConfig] = useState<PlatformConfig>(DEFAULT_CONFIG);
  const [us, setUs] = useState<UsReferenceResponse | null>(null);
  const [bt, setBt] = useState<BacktestResponse | null>(null);
  const [picks, setPicks] = useState<PicksResponse | null>(null);
  const [watch, setWatch] = useLocalStorage<string[]>("watchlist", []);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchRisk().then(setResult);
    fetchConfig().then(setConfig);
    fetchUsReference().then(setUs);
    fetchBacktest(20).then(setBt);
    fetchPicks().then((r) => setPicks(r.data));
  }, []);

  function toggleWatch(ticker: string) {
    setWatch((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker],
    );
  }

  async function handleRefresh() {
    setRefreshing(true);
    const r = await refreshRisk();
    setResult(r);
    setRefreshing(false);
  }

  if (!result) {
    return (
      <div className="flex min-h-screen items-center justify-center text-subtle">
        載入中…
      </div>
    );
  }

  const { data, usedFallback } = result;
  const { margin_institutional: mi, per, volatility: vol } = data.signals;

  return (
    <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Header
          updatedAt={data.updated_at}
          dataSource={data.data_source}
          usedFallback={usedFallback}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />

        {/* 模組B：綜合風險溫度計 */}
        <RiskGauge composite={data.composite} />

        {/* 模組A：三大前兆燈號 */}
        <h2 className="mb-3 mt-8 text-lg font-semibold text-ink">三大前兆監測</h2>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          <SignalCard
            index={1}
            title="融資 × 法人背離"
            subtitle="散戶融資創高、法人悄悄在賣——聰明錢出貨的訊號。"
            light={mi.light}
            score={mi.score}
            metrics={[
              { label: "融資餘額", value: fmtNum(mi.margin_latest, 0) },
              { label: "法人10日累計", value: fmtNum(mi.inst_cum_latest, 0), emphasis: mi.inst_selling },
              { label: "背離指標", value: fmtNum(mi.divergence, 2), emphasis: true },
              { label: "融資創60日高", value: mi.margin_high ? "是" : "否", emphasis: mi.margin_high },
            ]}
            note="背離指標 = z(融資20日變化) − z(法人10日累計淨買超)。融資創高且法人淨賣 → 紅燈。"
          >
            <MarginChart data={mi.series} />
          </SignalCard>

          <SignalCard
            index={2}
            title="本益比偏離歷史均值"
            subtitle="過熱時總有人用「這次不一樣」合理化高本益比＝放棄安全邊際。"
            light={per.light}
            score={per.score}
            metrics={[
              { label: "目前 P/E", value: fmtNum(per.current, 2), emphasis: true },
              { label: "歷史均值", value: fmtNum(per.mean, 2) },
              { label: "偏離 σ", value: `${per.sigma >= 0 ? "+" : ""}${fmtNum(per.sigma, 2)}σ`, emphasis: true },
              { label: "歷史百分位", value: `${fmtNum(per.pctile, 0)}%` },
            ]}
            note="近10年 P/E 百分位 / σ 偏離。> +1σ 或前20% → 黃；> +2σ 或前5% → 紅。"
          >
            <PerChart data={per.series} />
          </SignalCard>

          <SignalCard
            index={3}
            title="波動率極低（過度樂觀）"
            subtitle="反直覺：隱含波動率極低＝大家覺得沒風險、毫不防備，黑天鵝一來反應劇烈。"
            light={vol.light}
            score={vol.score}
            metrics={[
              { label: "波動率", value: fmtNum(vol.current, 2), emphasis: true },
              { label: "近一年分位", value: `${fmtNum(vol.pctile, 0)}%`, emphasis: true },
              { label: "判讀", value: "低波動＝高風險" },
              { label: "資料", value: vol.is_mock ? "mock（待接 TAIFEX）" : "實資料" },
            ]}
            note={
              vol.is_mock
                ? "TODO：台指波動率(VIXTWN) 尚未串接 TAIFEX，目前以 mock 佔位。最低10%→紅、10–25%→黃。"
                : "最低10%→紅、10–25%→黃。"
            }
          >
            <VixChart data={vol.series} />
          </SignalCard>
        </div>

        {/* 模組E：每日選股（價值・動能・存股 三風格融合） */}
        {picks && (
          <DailyPicks data={picks} watch={watch} onToggleWatch={toggleWatch} />
        )}

        {/* 我的追蹤清單（localStorage） */}
        {picks && (
          <Watchlist universe={picks.universe} watch={watch} onToggleWatch={toggleWatch} />
        )}

        {/* 模組C：倉位管理四鐵律 */}
        <div className="mt-8">
          <ModuleC config={config.position} compositeLight={data.composite.light} />
        </div>

        {/* 模組D：兩大隱形坑計算機 */}
        <h2 className="mb-3 mt-8 text-lg font-semibold text-ink">兩大隱形坑計算機</h2>
        <ModuleD tax={config.tax} etf={config.etf} />

        {/* Phase 3：美股對照指標 */}
        {us && (
          <div className="mt-8">
            <UsReference data={us} />
          </div>
        )}

        {/* Phase 3：風險分數歷史回測 */}
        {bt && (
          <div className="mt-8">
            <Backtest initial={bt} />
          </div>
        )}

        <footer className="mt-8 text-center text-xs leading-relaxed text-subtle">
          {data.disclaimer}
          <br />
          指標門檻（σ、百分位、天數、費率）皆為可調參數；稅務 / 健保費率屬政策，請定期確認最新法規。
        </footer>
      </div>
    </div>
  );
}
