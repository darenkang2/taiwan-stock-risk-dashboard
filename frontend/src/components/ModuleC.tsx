import type { ReactNode } from "react";
import type { Light } from "../types";
import type { PlatformConfig } from "../lib/config";
import { useLocalStorage } from "../lib/useLocalStorage";
import { fmtNum } from "../lib/format";
import { LIGHT_COLOR } from "../lib/light";
import NumberField from "./NumberField";

interface Props {
  config: PlatformConfig["position"];
  compositeLight: Light;
}

interface State {
  totalFunds: number | "";
  shortTermNeeds: number | "";
  holdings: number | "";
  canEndureDrop: boolean;
  noMargin: boolean;
  monthlyExpense: number | "";
  currentFund: number | "";
  idleChecked: boolean;
  emergencyChecked: boolean;
}

const INITIAL: State = {
  totalFunds: "",
  shortTermNeeds: "",
  holdings: "",
  canEndureDrop: false,
  noMargin: false,
  monthlyExpense: "",
  currentFund: "",
  idleChecked: false,
  emergencyChecked: false,
};

const num = (v: number | "") => (v === "" ? 0 : v);

function Rule({
  n,
  title,
  checked,
  onToggle,
  children,
}: {
  n: number;
  title: string;
  checked: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-100 p-4">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-sm font-semibold text-ink">
          鐵律 {n}：{title}
        </h4>
        <label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-xs text-subtle">
          <input
            type="checkbox"
            checked={checked}
            onChange={onToggle}
            className="h-4 w-4 accent-risk-green"
          />
          已檢核
        </label>
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function Result({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "warn" | "ok" }) {
  const color =
    tone === "warn" ? LIGHT_COLOR.red : tone === "ok" ? LIGHT_COLOR.green : "#1D1D1F";
  const bg =
    tone === "warn" ? `${LIGHT_COLOR.red}12` : tone === "ok" ? `${LIGHT_COLOR.green}12` : "#F5F5F7";
  return (
    <div className="mt-3 rounded-lg px-3 py-2 text-sm" style={{ backgroundColor: bg, color }}>
      {children}
    </div>
  );
}

export default function ModuleC({ config, compositeLight }: Props) {
  const [s, setS] = useLocalStorage<State>("module-c-state", INITIAL);
  const set = (patch: Partial<State>) => setS({ ...s, ...patch });

  const investCap = Math.max(0, num(s.totalFunds) - num(s.shortTermNeeds));
  const dropPct = config.stress_test_drop;
  const afterDrop = num(s.holdings) * (1 - dropPct);
  const loss = num(s.holdings) * dropPct;
  const fundMin = num(s.monthlyExpense) * config.emergency_fund_months_min;
  const fundMax = num(s.monthlyExpense) * config.emergency_fund_months_max;
  const fundProgress = fundMin > 0 ? Math.min(100, (num(s.currentFund) / fundMin) * 100) : 0;

  const checkedCount = [s.idleChecked, s.canEndureDrop, s.noMargin, s.emergencyChecked].filter(
    Boolean,
  ).length;

  const marginRed = compositeLight === "red";

  return (
    <section className="rounded-2xl bg-white p-5 shadow-card sm:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">倉位管理四鐵律</h2>
          <p className="mt-0.5 text-xs text-subtle">
            多頭末段，正確作法不是滿倉、也不是空倉，而是做好倉位管理。
          </p>
        </div>
        <span className="rounded-full bg-canvas px-3 py-1 text-sm font-medium text-ink">
          {checkedCount} / 4 已檢核
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* 鐵律1 閒置資金檢核 */}
        <Rule n={1} title="只用閒置資金投資" checked={s.idleChecked} onToggle={() => set({ idleChecked: !s.idleChecked })}>
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="手上可運用總資金" value={s.totalFunds} onChange={(v) => set({ totalFunds: v })} suffix="元" />
            <NumberField label="3–5 年內需用到的資金" value={s.shortTermNeeds} onChange={(v) => set({ shortTermNeeds: v })} suffix="元" />
          </div>
          <Result>
            建議可投資上限（閒置資金）約 <b className="tabular-nums">{fmtNum(investCap)}</b> 元
            <div className="mt-0.5 text-xs text-subtle">只用 3–5 年內用不到的閒置資金投資；有短期資金壓力時絕不加碼。</div>
          </Result>
        </Rule>

        {/* 鐵律2 -60% 壓力測試 */}
        <Rule n={2} title="進場前先算最壞情況" checked={s.canEndureDrop} onToggle={() => set({ canEndureDrop: !s.canEndureDrop })}>
          <NumberField label="目前持股市值" value={s.holdings} onChange={(v) => set({ holdings: v })} suffix="元" />
          <Result tone={num(s.holdings) > 0 && !s.canEndureDrop ? "warn" : "neutral"}>
            假設大跌 {Math.round(dropPct * 100)}%：市值剩 <b className="tabular-nums">{fmtNum(afterDrop)}</b> 元
            （損失約 <b className="tabular-nums">{fmtNum(loss)}</b> 元）
            {num(s.holdings) > 0 && !s.canEndureDrop && (
              <div className="mt-1 text-xs font-medium">
                若這樣的生活撐不過 → 倉位可能過重。撐得過再勾選右上「已檢核」。
              </div>
            )}
          </Result>
        </Rule>

        {/* 鐵律3 融資紅線（與模組B連動） */}
        <Rule n={3} title="高估區間絕不使用融資" checked={s.noMargin} onToggle={() => set({ noMargin: !s.noMargin })}>
          <Result tone={marginRed ? "warn" : "neutral"}>
            {marginRed ? (
              <>
                目前綜合風險為 <b>🔴 高風險</b>：使用融資的風險報酬比偏差。
                <div className="mt-0.5 text-xs">融資放大下跌、還要付息，高檔承擔的風險報酬極差。</div>
              </>
            ) : (
              <>目前綜合風險非高估區間，但融資仍會放大波動，請審慎評估。</>
            )}
          </Result>
        </Rule>

        {/* 鐵律4 緊急備用金 */}
        <Rule n={4} title="緊急備用金獨立於投資帳戶" checked={s.emergencyChecked} onToggle={() => set({ emergencyChecked: !s.emergencyChecked })}>
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="每月生活費" value={s.monthlyExpense} onChange={(v) => set({ monthlyExpense: v })} suffix="元" />
            <NumberField label="目前備用金" value={s.currentFund} onChange={(v) => set({ currentFund: v })} suffix="元" />
          </div>
          <Result tone={fundMin > 0 && num(s.currentFund) >= fundMin ? "ok" : "neutral"}>
            目標：<b className="tabular-nums">{fmtNum(fundMin)}</b> ~ <b className="tabular-nums">{fmtNum(fundMax)}</b> 元
            （{config.emergency_fund_months_min}–{config.emergency_fund_months_max} 個月生活費）
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
              <div className="h-full rounded-full" style={{ width: `${fundProgress}%`, backgroundColor: LIGHT_COLOR.green }} />
            </div>
            <div className="mt-1 text-xs text-subtle">須與投資帳戶分開，放隨時可動用帳戶 — 下跌時不被迫賣股的底氣。</div>
          </Result>
        </Rule>
      </div>
    </section>
  );
}
