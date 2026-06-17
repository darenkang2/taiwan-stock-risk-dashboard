import { fmtDateTime } from "../lib/format";

interface Props {
  updatedAt: string;
  dataSource: string;
  usedFallback: boolean;
  onRefresh: () => void;
  refreshing: boolean;
}

export default function Header({
  updatedAt,
  dataSource,
  usedFallback,
  onRefresh,
  refreshing,
}: Props) {
  return (
    <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
          台股頂部風險儀表板
        </h1>
        <p className="mt-1 text-sm text-subtle">
          風險「觀測 / 提醒」工具 — 回答「現在多危險、該降到多少水位」，不做買賣建議。
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right text-xs text-subtle">
          <div>更新時間：{fmtDateTime(updatedAt)}</div>
          <div>
            資料來源：
            <span className="font-medium text-ink">
              {dataSource === "mock" ? "假資料 (mock)" : dataSource}
            </span>
            {usedFallback && (
              <span className="ml-1 text-risk-yellow">（後端未連線，前端假資料）</span>
            )}
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white shadow-sm transition active:scale-95 disabled:opacity-50"
        >
          {refreshing ? "更新中…" : "重新整理"}
        </button>
      </div>
    </header>
  );
}
