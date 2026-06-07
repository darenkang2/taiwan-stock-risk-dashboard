"""前兆3：波動率極低（市場過度樂觀）。

反直覺：低波動＝大家覺得沒風險、毫不防備＝高風險。
邏輯（PRD，可參數化）：
  VIX 落在近一年最低 10% 區間 → 🔴
  最低 10–25% 區間 → 🟡
  其餘 → 🟢
子分數 (0–100) = 100 − 百分位（越低波動＝風險越高）。

⚠️ MVP：台指波動率(VIXTWN) 尚未串接 TAIFEX，序列以 mock 佔位，is_mock=True。
   TODO: 串接 TAIFEX 期交所 VIXTWN 後改為實資料。
"""
from __future__ import annotations

import numpy as np

from ..config import Thresholds, Windows
from ..data import MarketData
from ..schemas import Light, VixPoint, VolatilitySignal
from .utils import percentile_rank


def _history(vix: np.ndarray, w: Windows) -> np.ndarray:
    return vix[-w.vix_history_days:] if vix.size > w.vix_history_days else vix


def subscore(vix: np.ndarray, w: Windows) -> float:
    if vix.size == 0:
        return 50.0
    hist = _history(vix, w)
    return 100.0 - percentile_rank(hist, float(vix[-1]))


def _light(pctile: float, t: Thresholds) -> Light:
    if pctile <= t.vix_pctile_red:
        return "red"
    if pctile <= t.vix_pctile_yellow:
        return "yellow"
    return "green"


def evaluate(data: MarketData, w: Windows, t: Thresholds,
             series_days: int = 252, is_mock: bool = True) -> VolatilitySignal:
    vix = np.array(data.vix.values, dtype=float)
    dates = data.vix.dates
    hist = _history(vix, w)

    current = float(vix[-1])
    pctile = percentile_rank(hist, current)
    light = _light(pctile, t)

    p10 = float(np.percentile(hist, t.vix_pctile_red))
    p25 = float(np.percentile(hist, t.vix_pctile_yellow))

    n = min(series_days, len(vix))
    series = [
        VixPoint(date=d, vix=round(float(v), 2), p10=round(p10, 2), p25=round(p25, 2))
        for d, v in zip(dates[-n:], vix[-n:])
    ]

    return VolatilitySignal(
        light=light,
        score=round(100.0 - pctile, 1),
        current=round(current, 2),
        pctile=round(pctile, 1),
        is_mock=is_mock,
        series=series,
    )
