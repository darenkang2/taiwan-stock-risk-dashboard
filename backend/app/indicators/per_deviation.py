"""前兆2：本益比偏離歷史均值。

邏輯（PRD，可參數化）：
  取近 10 年 P/E，算當前值的百分位 / 標準差偏離。
  🟡 偏離 > +1σ 或落在歷史前 20%（百分位 ≥ 80）
  🔴 偏離 > +2σ 或落在歷史前 5%（百分位 ≥ 95）
子分數 (0–100) = 歷史百分位（越高＝越貴＝風險越高）。
"""
from __future__ import annotations

import numpy as np

from ..config import Thresholds, Windows
from ..data import MarketData
from ..schemas import Light, PerPoint, PerSignal
from .utils import percentile_rank, zscore


def _history(per: np.ndarray, w: Windows) -> np.ndarray:
    days = w.per_history_years * 252
    return per[-days:] if per.size > days else per


def subscore(per: np.ndarray, w: Windows) -> float:
    if per.size == 0:
        return 50.0
    hist = _history(per, w)
    return percentile_rank(hist, float(per[-1]))


def _light(sigma: float, pctile: float, t: Thresholds) -> Light:
    if sigma > t.per_sigma_red or pctile >= t.per_pctile_red:
        return "red"
    if sigma > t.per_sigma_yellow or pctile >= t.per_pctile_yellow:
        return "yellow"
    return "green"


def evaluate(data: MarketData, w: Windows, t: Thresholds,
             series_days: int = 252) -> PerSignal:
    per = np.array(data.per.values, dtype=float)
    dates = data.per.dates
    hist = _history(per, w)

    current = float(per[-1])
    mean = float(np.mean(hist))
    std = float(np.std(hist))
    sigma = zscore(hist, current)
    pctile = percentile_rank(hist, current)
    light = _light(sigma, pctile, t)

    n = min(series_days, len(per))
    per_tail = per[-n:]
    dates_tail = dates[-n:]
    series = [
        PerPoint(
            date=d,
            per=round(float(v), 2),
            mean=round(mean, 2),
            upper1=round(mean + std, 2),
            lower1=round(mean - std, 2),
            upper2=round(mean + 2 * std, 2),
            lower2=round(mean - 2 * std, 2),
        )
        for d, v in zip(dates_tail, per_tail)
    ]

    return PerSignal(
        light=light,
        score=round(pctile, 1),
        current=round(current, 2),
        mean=round(mean, 2),
        sigma=round(sigma, 2),
        pctile=round(pctile, 1),
        series=series,
    )
