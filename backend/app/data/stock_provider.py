"""個股資料快照層：為選股策略提供每檔股票的價格序列與基本面欄位。

來源：
  - 台股：FinMind `TaiwanStockPrice`（收盤序列）+ `TaiwanStockPER`（PER / PBR / 殖利率）。
  - 美股：yfinance（收盤序列 + 基本面，best-effort）。
  - 未設定 token / 抓取失敗：以確定性 mock 佔位（per 檔退回），確保掃描永遠有結果。

設計原則同既有 provider：任一檔抓取失敗不應中斷整體掃描，逐檔 fallback。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from ..config import Settings, resolve_data_source
from .universe import Stock, full_universe, tw_universe, us_universe

logger = logging.getLogger(__name__)


@dataclass
class StockSnapshot:
    """單一個股的最小必要資料，供 stock_strategy 計算選股分數。"""
    stock: Stock
    dates: list[str]                 # 交易日，遞增
    closes: list[float]              # 收盤價，與 dates 等長、遞增
    per: float | None = None         # 本益比
    pb: float | None = None          # 股價淨值比
    dividend_yield: float | None = None  # 現金殖利率（%）
    is_mock: bool = False            # 此檔是否為 mock 佔位
    extras: dict = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────
# 對外入口
# ──────────────────────────────────────────────────────────────────────────
def get_stock_snapshots(settings: Settings) -> tuple[list[StockSnapshot], str]:
    """回傳 (snapshots, data_source)。data_source: mock | live | live(partial)。"""
    source = resolve_data_source(settings)
    if source == "mock":
        return generate_mock_snapshots(full_universe()), "mock"

    snaps: list[StockSnapshot] = []
    live_count = 0

    # 台股：FinMind
    for s in tw_universe():
        snap = _try(lambda: _fetch_tw(s, settings))
        if snap is not None:
            snaps.append(snap)
            live_count += 1
        else:
            snaps.append(_mock_one(s))

    # 美股：yfinance（批次抓價 + 逐檔基本面）
    us_list = us_universe()
    us_prices = _try(lambda: _fetch_us_prices(us_list)) or {}
    for s in us_list:
        px = us_prices.get(s.ticker)
        if px and len(px[1]) >= 130:
            dates, closes = px
            per, pb, dy = _try(lambda: _fetch_us_fundamentals(s.ticker)) or (None, None, None)
            snaps.append(StockSnapshot(s, dates, closes, per, pb, dy))
            live_count += 1
        else:
            snaps.append(_mock_one(s))

    if live_count == 0:
        logger.warning("個股即時抓取全數失敗，整體 fallback mock")
        return generate_mock_snapshots(full_universe()), "mock"
    source_label = "live" if live_count == len(snaps) else "live(partial)"
    return snaps, source_label


def _try(fn):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — 逐檔/批次失敗皆退回 mock
        logger.warning("個股抓取失敗，退回 mock：%s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────
# 台股：FinMind
# ──────────────────────────────────────────────────────────────────────────
def _fetch_tw(stock: Stock, settings: Settings) -> StockSnapshot:
    import httpx

    cfg = settings.finmind
    start = (date.today() - timedelta(days=560)).isoformat()

    def _get(dataset: str) -> list[dict]:
        params = {"dataset": dataset, "data_id": stock.ticker, "start_date": start}
        if cfg.token:
            params["token"] = cfg.token
        resp = httpx.get(cfg.base_url, params=params, timeout=cfg.timeout_seconds)
        resp.raise_for_status()
        return (resp.json() or {}).get("data") or []

    price_rows = _get("TaiwanStockPrice")
    rows = [r for r in price_rows if r.get("close") not in (None, "", 0)]
    rows.sort(key=lambda r: r["date"])
    dates = [r["date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    if len(closes) < 130:
        raise ValueError(f"{stock.ticker} 價格資料不足")

    per = pb = dy = None
    per_rows = _get("TaiwanStockPER")
    if per_rows:
        last = sorted(per_rows, key=lambda r: r.get("date", ""))[-1]
        per = _f(last.get("PER"))
        pb = _f(last.get("PBR"))
        dy = _f(last.get("dividend_yield"))

    return StockSnapshot(stock, dates, closes, per, pb, dy)


# ──────────────────────────────────────────────────────────────────────────
# 美股：yfinance
# ──────────────────────────────────────────────────────────────────────────
def _fetch_us_prices(stocks: list[Stock]) -> dict[str, tuple[list[str], list[float]]]:
    import yfinance as yf

    symbols = [s.ticker for s in stocks]
    df = yf.download(
        symbols, period="2y", interval="1d",
        auto_adjust=True, progress=False, group_by="ticker", threads=True,
    )
    out: dict[str, tuple[list[str], list[float]]] = {}
    for sym in symbols:
        try:
            sub = df[sym]["Close"].dropna() if len(symbols) > 1 else df["Close"].dropna()
        except (KeyError, TypeError):
            continue
        if sub.empty:
            continue
        dates = [d.strftime("%Y-%m-%d") for d in sub.index]
        out[sym] = (dates, [float(x) for x in sub.values])
    return out


def _fetch_us_fundamentals(symbol: str) -> tuple[float | None, float | None, float | None]:
    import yfinance as yf

    info = yf.Ticker(symbol).info or {}
    per = _f(info.get("trailingPE"))
    pb = _f(info.get("priceToBook"))
    dy = info.get("dividendYield")
    dy = float(dy) * 100 if dy not in (None, "") else None  # yfinance 殖利率為小數
    return per, pb, dy


def _f(v) -> float | None:
    try:
        if v in (None, ""):
            return None
        f = float(v)
        return f if f == f else None  # 過濾 NaN
    except (TypeError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────────────
# Mock：確定性、且刻意製造四種典型情境，方便 demo / 測試呈現多樣性
#   regime 0 價值股（超賣、跌破均線、低 PER、殖利率中上）
#   regime 1 動能股（多頭排列、貼近高點、PER 偏高）
#   regime 2 存股（低波動、高殖利率、走勢平穩）
#   regime 3 過熱股（RSI 過熱、PER 很高 → 風險警示）
# ──────────────────────────────────────────────────────────────────────────
def generate_mock_snapshots(stocks: list[Stock]) -> list[StockSnapshot]:
    return [_mock_one(s) for s in stocks]


def _mock_one(stock: Stock) -> StockSnapshot:
    seed = abs(hash(stock.ticker)) % (2**32)
    rng = np.random.default_rng(seed)
    regime = seed % 4
    n = 300
    dates = _trading_days(n, date.today())
    t = np.arange(n)
    base = 30 + (seed % 200)  # 起始價

    if regime == 0:  # 價值 / 超賣
        trend = -0.10 * t / n
        closes = base * (1 + trend) * (1 + np.cumsum(rng.normal(-0.0006, 0.013, n)))
        closes[-15:] *= np.linspace(1.0, 0.90, 15)  # 末段跌深 → RSI 超賣
        per, pb, dy = 9.5 + rng.normal(0, 1), 1.1, 4.2 + rng.normal(0, 0.5)
    elif regime == 1:  # 動能 / 多頭
        trend = 0.45 * t / n
        closes = base * (1 + trend) * (1 + np.cumsum(rng.normal(0.0011, 0.012, n)))
        per, pb, dy = 28 + rng.normal(0, 3), 4.5, 1.1 + rng.normal(0, 0.3)
    elif regime == 2:  # 存股 / 低波動高息
        closes = base * (1 + 0.06 * t / n) * (1 + np.cumsum(rng.normal(0.0002, 0.006, n)))
        per, pb, dy = 15 + rng.normal(0, 1.5), 1.8, 5.5 + rng.normal(0, 0.6)
    else:            # 過熱 / 風險警示
        trend = 0.70 * t / n
        closes = base * (1 + trend) * (1 + np.cumsum(rng.normal(0.0016, 0.018, n)))
        closes[-12:] *= np.linspace(1.0, 1.16, 12)  # 末段急拉 → RSI 過熱
        per, pb, dy = 46 + rng.normal(0, 5), 8.0, 0.4 + rng.normal(0, 0.2)

    closes = np.maximum(closes, 1.0)
    return StockSnapshot(
        stock=stock,
        dates=dates,
        closes=[round(float(x), 2) for x in closes],
        per=round(float(max(per, 1)), 2),
        pb=round(float(max(pb, 0.1)), 2),
        dividend_yield=round(float(max(dy, 0)), 2),
        is_mock=True,
    )


def _trading_days(n: int, end: date) -> list[str]:
    days: list[str] = []
    d = end
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d -= timedelta(days=1)
    return list(reversed(days))
