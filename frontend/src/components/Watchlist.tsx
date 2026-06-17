import { useMemo, useState } from "react";
import type { StockPick } from "../types";
import PickCard from "./PickCard";

interface Props {
  universe: StockPick[];
  watch: string[];
  onToggleWatch: (ticker: string) => void;
}

export default function Watchlist({ universe, watch, onToggleWatch }: Props) {
  const [query, setQuery] = useState("");

  const byTicker = useMemo(() => {
    const m = new Map<string, StockPick>();
    universe.forEach((p) => m.set(p.ticker, p));
    return m;
  }, [universe]);

  const watched = watch.map((t) => byTicker.get(t)).filter((p): p is StockPick => Boolean(p));

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return universe
      .filter(
        (p) =>
          !watch.includes(p.ticker) &&
          (p.ticker.toLowerCase().includes(q) || p.name.toLowerCase().includes(q)),
      )
      .slice(0, 8);
  }, [query, universe, watch]);

  return (
    <section className="mt-10">
      <div>
        <h2 className="text-lg font-semibold text-ink">我的追蹤清單</h2>
        <p className="mt-1 text-xs leading-relaxed text-subtle">
          自選關注標的，每日同步最新評分與指標。清單儲存在本機瀏覽器（localStorage），不需登入。
        </p>
      </div>

      {/* 搜尋加入 */}
      <div className="relative mt-4 max-w-md">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="輸入代號或名稱加入（如 2330、台積電、AAPL）"
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-ink shadow-sm outline-none focus:border-gray-300"
        />
        {suggestions.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-xl border border-gray-100 bg-white shadow-card">
            {suggestions.map((p) => (
              <li key={p.ticker}>
                <button
                  type="button"
                  onClick={() => {
                    onToggleWatch(p.ticker);
                    setQuery("");
                  }}
                  className="flex w-full items-center justify-between px-4 py-2 text-left text-sm transition hover:bg-gray-50"
                >
                  <span className="text-ink">
                    {p.name}
                    <span className="ml-2 text-xs text-subtle">
                      {p.market === "tw" ? "台股" : "美股"} {p.ticker}
                    </span>
                  </span>
                  <span className="text-xs text-subtle">選股分 {p.score}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {watched.length === 0 ? (
        <p className="mt-5 rounded-2xl bg-white px-4 py-8 text-center text-sm text-subtle shadow-card">
          尚未加入任何追蹤標的。用上方搜尋框，或在「每日選股」卡片點 ☆ 加入。
        </p>
      ) : (
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {watched.map((p) => (
            <PickCard key={p.ticker} pick={p} watched onToggleWatch={onToggleWatch} />
          ))}
        </div>
      )}
    </section>
  );
}
