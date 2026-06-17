import type { PlatformConfig } from "../lib/config";
import { useLocalStorage } from "../lib/useLocalStorage";
import { fmtNum } from "../lib/format";
import { LIGHT_COLOR } from "../lib/light";
import NumberField from "./NumberField";

interface Props {
  tax: PlatformConfig["tax"];
  etf: PlatformConfig["etf"];
}

interface State {
  // ETF 折溢價
  price: number | "";
  nav: number | "";
  // 股利稅 + 二代健保
  annualDividend: number | "";
  maxSingle: number | "";
  holdingValue: number | "";
  bracket: number; // 綜所稅級距 %
}

const INITIAL: State = {
  price: "",
  nav: "",
  annualDividend: "",
  maxSingle: "",
  holdingValue: "",
  bracket: 0,
};

const BRACKETS = [0, 5, 12, 20, 30, 40]; // 綜所稅級距 %
const num = (v: number | "") => (v === "" ? 0 : v);

export default function ModuleD({ tax, etf }: Props) {
  const [s, setS] = useLocalStorage<State>("module-d-state", INITIAL);
  const set = (patch: Partial<State>) => setS({ ...s, ...patch });

  // ── ETF 折溢價 ──
  const navVal = num(s.nav);
  const premiumPct = navVal > 0 ? ((num(s.price) - navVal) / navVal) * 100 : 0;
  const isDiscount = premiumPct < 0;
  const discountAlert = navVal > 0 && -premiumPct > etf.discount_alert_threshold;

  // ── 股利稅 + 二代健保補充保費 ──
  const supplementary =
    num(s.maxSingle) >= tax.supplementary_premium_threshold
      ? Math.min(num(s.maxSingle), tax.supplementary_premium_cap) * tax.supplementary_premium_rate
      : 0;
  const dividendTax = num(s.annualDividend) * (s.bracket / 100);
  const hv = num(s.holdingValue);
  const grossYield = hv > 0 ? (num(s.annualDividend) / hv) * 100 : 0;
  const netYield = hv > 0 ? ((num(s.annualDividend) - supplementary - dividendTax) / hv) * 100 : 0;

  return (
    <section className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      {/* ETF 折溢價監控 */}
      <div className="rounded-2xl bg-white p-5 shadow-card sm:p-6">
        <h3 className="text-base font-semibold text-ink">ETF 折溢價監控</h3>
        <p className="mt-0.5 text-xs text-subtle">
          恐慌暴跌時 ETF 市價可能大幅低於淨值（折價），恐慌賣出＝下跌 + 折價雙重虧損。
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <NumberField label="市價" value={s.price} onChange={(v) => set({ price: v })} suffix="元" />
          <NumberField label="淨值 NAV" value={s.nav} onChange={(v) => set({ nav: v })} suffix="元" placeholder="可手動輸入" />
        </div>
        <div
          className="mt-4 rounded-lg px-3 py-3 text-sm"
          style={{ backgroundColor: discountAlert ? `${LIGHT_COLOR.red}12` : "#F5F5F7" }}
        >
          <div className="flex items-baseline justify-between">
            <span className="text-subtle">{isDiscount ? "折價" : "溢價"}</span>
            <span
              className="text-xl font-bold tabular-nums"
              style={{ color: discountAlert ? LIGHT_COLOR.red : "#1D1D1F" }}
            >
              {premiumPct >= 0 ? "+" : ""}
              {fmtNum(premiumPct, 2)}%
            </span>
          </div>
          {discountAlert && (
            <div className="mt-1 text-xs font-medium" style={{ color: LIGHT_COLOR.red }}>
              折價已超過 {etf.discount_alert_threshold}% 門檻：恐慌時賣出將承擔額外折價損失。
            </div>
          )}
        </div>
        <p className="mt-3 text-[11px] text-subtle">
          NAV 建議取自各投信公告 / 集保；MVP 先採手動輸入版。
        </p>
      </div>

      {/* 股利稅 + 二代健保補充保費 */}
      <div className="rounded-2xl bg-white p-5 shadow-card sm:p-6">
        <h3 className="text-base font-semibold text-ink">股利稅 ＋ 二代健保補充保費</h3>
        <p className="mt-0.5 text-xs text-subtle">
          算入隱形稅務成本後，稅後報酬可能不如帳面殖利率。
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <NumberField label="年度股利總額" value={s.annualDividend} onChange={(v) => set({ annualDividend: v })} suffix="元" />
          <NumberField label="單次最大一筆股利" value={s.maxSingle} onChange={(v) => set({ maxSingle: v })} suffix="元" />
          <NumberField label="持有市值" value={s.holdingValue} onChange={(v) => set({ holdingValue: v })} suffix="元" />
          <label className="block">
            <span className="text-xs text-subtle">綜所稅級距（可選）</span>
            <select
              value={s.bracket}
              onChange={(e) => set({ bracket: Number(e.target.value) })}
              className="mt-1 w-full rounded-xl border border-gray-200 bg-canvas px-3 py-2 text-base font-medium text-ink outline-none focus:border-ink/30"
            >
              {BRACKETS.map((b) => (
                <option key={b} value={b}>
                  {b}%
                </option>
              ))}
            </select>
          </label>
        </div>

        <dl className="mt-4 space-y-2 rounded-lg bg-canvas px-3 py-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-subtle">二代健保補充保費</dt>
            <dd className="font-medium tabular-nums" style={{ color: supplementary > 0 ? LIGHT_COLOR.yellow : "#1D1D1F" }}>
              {fmtNum(supplementary)} 元
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-subtle">股利所得稅（簡化）</dt>
            <dd className="font-medium tabular-nums">{fmtNum(dividendTax)} 元</dd>
          </div>
          <div className="flex justify-between border-t border-gray-200 pt-2">
            <dt className="text-subtle">帳面殖利率</dt>
            <dd className="font-medium tabular-nums">{fmtNum(grossYield, 2)}%</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-subtle">稅後實際報酬率</dt>
            <dd className="text-base font-bold tabular-nums" style={{ color: LIGHT_COLOR.green }}>
              {fmtNum(netYield, 2)}%
            </dd>
          </div>
        </dl>

        <p className="mt-3 text-[11px] leading-relaxed text-subtle">
          補充保費：單次給付逾 {fmtNum(tax.supplementary_premium_threshold)} 元者 ×{" "}
          {fmtNum(tax.supplementary_premium_rate * 100, 2)}%（單次上限{" "}
          {fmtNum(tax.supplementary_premium_cap)} 元）。{tax.note}
        </p>
      </div>
    </section>
  );
}
