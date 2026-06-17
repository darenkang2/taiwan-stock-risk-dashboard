"""Phase 3 — 美股對照指標（國際對照，可選）。

三個指標各輸出燈號 + 百分位 + 近一年趨勢，僅作國際對照，不併入台股綜合分數：
  - ^VIX：美股波動率（低＝過度樂觀，反直覺，與台股前兆3 同邏輯）
  - Shiller CAPE：週期調整本益比，越高越貴（百分位高 → 風險高）
  - 巴菲特指標：股市總市值 / GDP（%），越高越貴

⚠️ 目前資料為 mock 佔位（TODO 實接 ^VIX / multpl.com / FRED）。
"""
from __future__ import annotations

import numpy as np

from ..config import Thresholds, Windows
from ..data import UsReference
from ..schemas import Light, UsIndicator, UsReferenceResponse
from .utils import percentile_rank


def _series_tail(dates: list[str], values: np.ndarray, n: int) -> list[dict]:
    n = min(n, len(values))
    return [{"date": d, "value": round(float(v), 2)} for d, v in zip(dates[-n:], values[-n:])]


def _high_is_risk_light(pctile: float, t: Thresholds) -> Light:
    if pctile >= t.per_pctile_red:
        return "red"
    if pctile >= t.per_pctile_yellow:
        return "yellow"
    return "green"


def _low_vix_light(pctile: float, t: Thresholds) -> Light:
    if pctile <= t.vix_pctile_red:
        return "red"
    if pctile <= t.vix_pctile_yellow:
        return "yellow"
    return "green"


def _indicator(name: str, dates: list[str], arr: np.ndarray, light: Light,
               pctile: float, score: float, unit: str, hint: str) -> UsIndicator:
    return UsIndicator(
        name=name,
        light=light,
        current=round(float(arr[-1]), 2),
        pctile=round(pctile, 1),
        score=round(score, 1),
        unit=unit,
        hint=hint,
        series=_series_tail(dates, arr, 252),
    )


def evaluate(ref: UsReference, w: Windows, t: Thresholds) -> UsReferenceResponse:
    vix = np.array(ref.vix.values, dtype=float)
    cape = np.array(ref.cape.values, dtype=float)
    buf = np.array(ref.buffett.values, dtype=float)

    vix_hist = vix[-w.vix_history_days:] if vix.size > w.vix_history_days else vix
    vix_pct = percentile_rank(vix_hist, float(vix[-1]))
    cape_pct = percentile_rank(cape, float(cape[-1]))
    buf_pct = percentile_rank(buf, float(buf[-1]))

    return UsReferenceResponse(
        source=ref.source,
        is_mock=ref.source == "mock",
        indicators=[
            _indicator("美股 VIX", ref.vix.dates, vix, _low_vix_light(vix_pct, t),
                       vix_pct, 100.0 - vix_pct, "", "低波動＝市場過度樂觀（反直覺）"),
            _indicator("Shiller CAPE", ref.cape.dates, cape, _high_is_risk_light(cape_pct, t),
                       cape_pct, cape_pct, "倍", "週期調整本益比，越高越貴"),
            _indicator("巴菲特指標", ref.buffett.dates, buf, _high_is_risk_light(buf_pct, t),
                       buf_pct, buf_pct, "%", "股市總市值 / GDP，越高越貴"),
        ],
    )
