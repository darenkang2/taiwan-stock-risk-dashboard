"""模組 E：每日選股策略（價值/均值回歸 + 動能/趨勢 + 存股/防禦 三風格融合）。

設計哲學同全專案：所有門檻為「量化詮釋、非保證有效」，故全部集中於 config 的
StrategyConfig，方便日後校準。本模組為純函式（numpy in、StockPick out），易於測試。

每檔輸出：
  - score 0–100：三風格子分數依權重融合（權重可調，預設等權）。
  - scores：三個子分數（透明可檢視）。
  - risk_light：個股風險燈（過熱 / 偏貴；大盤紅燈時整體上調），供「風險警示」清單。
  - tags / rationale：白話標籤與一句話理由（皆為條件描述，非投資建議）。
"""
from __future__ import annotations

import numpy as np

from ..config import StrategyConfig
from ..data.stock_provider import StockSnapshot
from ..schemas import Light, PickScores, StockPick, Style


# ── 小工具 ────────────────────────────────────────────────────────────────
def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _lin(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """線性映射並夾在 [min(y0,y1), max(y0,y1)]。"""
    if x1 == x0:
        return y0
    y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return _clamp(y, min(y0, y1), max(y0, y1))


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    diff = np.diff(closes[-(period + 1):])
    gain = np.clip(diff, 0, None).mean()
    loss = -np.clip(diff, None, 0).mean()
    if loss == 0:
        return 100.0
    rs = gain / loss
    return float(100 - 100 / (1 + rs))


def _ma(closes: np.ndarray, n: int) -> float:
    if len(closes) < n:
        return float(closes.mean())
    return float(closes[-n:].mean())


# ── 主函式 ────────────────────────────────────────────────────────────────
def evaluate(snap: StockSnapshot, market_light: Light, cfg: StrategyConfig) -> StockPick:
    closes = np.asarray(snap.closes, dtype=float)
    price = float(closes[-1])
    change_pct = float((closes[-1] / closes[-2] - 1) * 100) if len(closes) >= 2 else 0.0

    rsi = _rsi(closes)
    ma20, ma60, ma120 = _ma(closes, 20), _ma(closes, 60), _ma(closes, 120)
    bias60 = (price / ma60 - 1) * 100 if ma60 else 0.0

    lookback = min(len(closes), cfg.high_window)
    high_52w = float(closes[-lookback:].max())
    below_high = (1 - price / high_52w) * 100 if high_52w else 0.0

    idx_3m = max(0, len(closes) - cfg.momentum_window)
    ret_3m = (price / closes[idx_3m] - 1) * 100 if closes[idx_3m] else 0.0

    rets = np.diff(closes[-cfg.vol_window:]) / closes[-cfg.vol_window:-1] \
        if len(closes) > cfg.vol_window else np.diff(closes) / closes[:-1]
    vol_annual = float(rets.std() * np.sqrt(252) * 100) if rets.size else 0.0

    per, dy = snap.per, snap.dividend_yield

    # ── 子分數：價值 / 均值回歸 ──────────────────────────────────────────
    per_score = _lin(per, cfg.per_cheap, cfg.per_rich, 100, 0) if per and per > 0 else 50.0
    rsi_value = _lin(rsi, cfg.rsi_oversold, cfg.rsi_overbought, 100, 0)
    pullback = _lin(bias60, cfg.pullback_deep, cfg.pullback_none, 100, 0)
    value = 0.40 * per_score + 0.35 * rsi_value + 0.25 * pullback

    # ── 子分數：動能 / 趨勢 ──────────────────────────────────────────────
    align = (int(price > ma20) + int(ma20 > ma60) + int(ma60 > ma120)) / 3 * 100
    ret_score = _lin(ret_3m, cfg.ret_weak, cfg.ret_strong, 0, 100)
    high_prox = _lin(below_high, 0, cfg.high_far, 100, 0)
    momentum = 0.40 * align + 0.35 * ret_score + 0.25 * high_prox

    # ── 子分數：存股 / 防禦 ──────────────────────────────────────────────
    yield_score = _lin(dy, 0, cfg.yield_high, 0, 100) if dy is not None else 0.0
    lowvol_score = _lin(vol_annual, cfg.vol_low, cfg.vol_high, 100, 0)
    dividend = 0.55 * yield_score + 0.45 * lowvol_score

    # ── 融合（權重正規化）────────────────────────────────────────────────
    wv, wm, wd = _norm_weights(cfg)
    score = wv * value + wm * momentum + wd * dividend

    sub = {"value": value, "momentum": momentum, "dividend": dividend}
    top_style: Style = max(sub, key=sub.get)  # type: ignore[assignment]

    # ── 個股風險燈（過熱 / 偏貴；大盤紅燈整體上調）──────────────────────
    overbought = _lin(rsi, 60, 85, 0, 100)
    expensive = _lin(per, cfg.per_rich, cfg.per_rich * 1.6, 0, 100) if per and per > 0 else 0.0
    risk_raw = 0.6 * overbought + 0.4 * expensive
    if market_light == "red":
        risk_raw += 15
    elif market_light == "yellow":
        risk_raw += 7
    risk_raw = _clamp(risk_raw)
    risk_light: Light = "red" if risk_raw >= 66 else "yellow" if risk_raw >= 40 else "green"

    tags = _build_tags(rsi, align, dy, per, vol_annual, below_high, ret_3m, price, ma60, cfg)
    ma_state = _ma_state(price, ma20, ma60, ma120)
    rationale = _rationale(top_style, sub, market_light)

    return StockPick(
        ticker=snap.stock.ticker,
        name=snap.stock.name,
        market=snap.stock.market,
        price=round(price, 2),
        change_pct=round(change_pct, 2),
        score=round(score, 1),
        scores=PickScores(
            value=round(value, 1), momentum=round(momentum, 1), dividend=round(dividend, 1),
        ),
        top_style=top_style,
        risk_light=risk_light,
        tags=tags,
        rationale=rationale,
        per=snap.per,
        pb=snap.pb,
        dividend_yield=snap.dividend_yield,
        rsi=round(rsi, 1),
        vol_annual=round(vol_annual, 1),
        ret_3m=round(ret_3m, 1),
        ma_state=ma_state,
        below_high_pct=round(below_high, 1),
        is_mock=snap.is_mock,
    )


def _norm_weights(cfg: StrategyConfig) -> tuple[float, float, float]:
    total = cfg.w_value + cfg.w_momentum + cfg.w_dividend
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return cfg.w_value / total, cfg.w_momentum / total, cfg.w_dividend / total


def normalized_weights(cfg: StrategyConfig) -> PickScores:
    wv, wm, wd = _norm_weights(cfg)
    return PickScores(value=round(wv, 4), momentum=round(wm, 4), dividend=round(wd, 4))


def _ma_state(price: float, ma20: float, ma60: float, ma120: float) -> str:
    if price > ma20 > ma60 > ma120:
        return "多頭排列（站上所有均線）"
    if price < ma20 < ma60 < ma120:
        return "空頭排列（跌破所有均線）"
    if price > ma60:
        return "中期偏多（站上季線）"
    return "中期偏弱（跌破季線）"


def _build_tags(rsi, align, dy, per, vol, below_high, ret_3m, price, ma60, cfg) -> list[str]:
    tags: list[str] = []
    if rsi <= cfg.rsi_oversold + 5:
        tags.append("超賣")
    if rsi >= cfg.rsi_overbought + 5:
        tags.append("過熱")
    if align >= 100:
        tags.append("多頭排列")
    elif price < ma60:
        tags.append("跌破季線")
    if dy is not None and dy >= cfg.yield_high * 0.8:
        tags.append("高殖利率")
    if per and 0 < per <= cfg.per_cheap + 2:
        tags.append("低本益比")
    if per and per >= cfg.per_rich:
        tags.append("本益比偏高")
    if vol <= cfg.vol_low + 3:
        tags.append("低波動")
    elif vol >= cfg.vol_high:
        tags.append("高波動")
    if below_high <= 3:
        tags.append("逼近52週高")
    if ret_3m >= cfg.ret_strong * 0.7:
        tags.append("強勢動能")
    return tags


_STYLE_LABEL = {"value": "價值/均值回歸", "momentum": "動能/趨勢", "dividend": "存股/防禦"}
_STYLE_DESC = {
    "value": "本益比與股價位階偏低、出現超賣，符合逢低布局條件",
    "momentum": "均線多頭、近期走勢強勢且貼近高點，符合順勢條件",
    "dividend": "殖利率較高且波動較低，符合穩健存股條件",
}


def _rationale(top_style: Style, sub: dict, market_light: Light) -> str:
    base = f"主要符合「{_STYLE_LABEL[top_style]}」：{_STYLE_DESC[top_style]}。"
    if market_light == "red":
        base += "（注意：目前大盤頂部風險偏高，留意整體系統性風險。）"
    return base
