"""前兆1：融資 × 法人背離。

邏輯（PRD，可參數化）：
  背離指標 = z(融資餘額 20 日變化) − z(法人近 10 日累計淨買超)
  燈號：
    🔴 融資餘額創 60 日新高 且 法人近 10 日累計淨賣超
    🟡 二者其一成立
    🟢 皆否
子分數 (0–100)：0.5 × 融資高檔百分位 + 0.5 × 法人賣壓分數，higher = 風險高。
"""
from __future__ import annotations

import numpy as np

from ..config import Windows
from ..data import MarketData
from ..schemas import Light, MarginPoint, MarginSignal
from .utils import clamp, percentile_rank, rolling_sum, zscore


def _margin_high_pctile(margin: np.ndarray, w: Windows) -> float:
    window = margin[-w.margin_high_days:]
    return percentile_rank(window, float(margin[-1]))


def _inst_risk_score(inst: np.ndarray, w: Windows) -> float:
    """法人累計淨買超 → 風險分數。淨賣（負）越深 → 分數越高。"""
    cum = rolling_sum(inst, w.inst_cumulative_days)
    z = zscore(cum, float(cum[-1]))
    # z=+3（大幅淨買）→ 0；z=-3（大幅淨賣）→ 100
    return clamp(50.0 - (100.0 / 6.0) * z)


def subscore(margin: np.ndarray, inst: np.ndarray, w: Windows) -> float:
    if margin.size < w.margin_high_days or inst.size < w.inst_cumulative_days + 1:
        return 50.0
    return clamp(0.5 * _margin_high_pctile(margin, w) + 0.5 * _inst_risk_score(inst, w))


def _light(margin_high: bool, inst_selling: bool) -> Light:
    if margin_high and inst_selling:
        return "red"
    if margin_high or inst_selling:
        return "yellow"
    return "green"


def evaluate(data: MarketData, w: Windows, series_days: int = 252) -> MarginSignal:
    margin = np.array(data.margin.values, dtype=float)
    inst = np.array(data.institutional.values, dtype=float)
    m_dates = data.margin.dates
    i_dates = data.institutional.dates

    # 融資創 60 日新高？
    high_window = margin[-w.margin_high_days:]
    margin_high = bool(margin[-1] >= high_window.max() - 1e-9)

    # 法人近 10 日累計淨買超
    inst_cum_latest = float(inst[-w.inst_cumulative_days:].sum())
    inst_selling = inst_cum_latest < 0

    # 背離指標 = z(融資20日變化) − z(法人10日累計淨買超)
    change_window = w.margin_change_days
    margin_changes = margin[change_window:] - margin[:-change_window]
    z_margin = zscore(margin_changes, float(margin[-1] - margin[-1 - change_window]))
    inst_cum = rolling_sum(inst, w.inst_cumulative_days)
    z_inst = zscore(inst_cum, float(inst_cum[-1]))
    divergence = z_margin - z_inst

    score = subscore(margin, inst, w)
    light = _light(margin_high, inst_selling)

    # 圖表序列：融資餘額 vs 法人累計買賣超（以法人各日對齊，取交集尾段）
    inst_rolling = rolling_sum(inst, w.inst_cumulative_days)
    # 對齊：rolling 後長度較短，取對應日期尾段
    n = min(series_days, len(inst_rolling), len(margin))
    margin_tail = margin[-n:]
    inst_cum_tail = inst_rolling[-n:]
    dates_tail = (i_dates if len(i_dates) >= n else m_dates)[-n:]
    series = [
        MarginPoint(date=d, margin=round(float(mv), 1), inst_cum=round(float(iv), 1))
        for d, mv, iv in zip(dates_tail, margin_tail, inst_cum_tail)
    ]

    return MarginSignal(
        light=light,
        score=round(score, 1),
        divergence=round(float(divergence), 2),
        margin_high=margin_high,
        inst_selling=inst_selling,
        margin_latest=round(float(margin[-1]), 1),
        inst_cum_latest=round(inst_cum_latest, 1),
        series=series,
    )
