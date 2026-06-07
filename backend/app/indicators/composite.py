"""模組B：綜合風險溫度計。

將三個子分數加權合成 0–100「頂部風險分數」（預設等權，權重可調）。
  0–40 綠（風險低）/ 40–70 黃（留意）/ 70–100 紅（高風險）
並計算近 90 日趨勢線（逐日重算子分數）。

所有對應文案一律用「觀測 / 參考」語氣，不下投資指令。
"""
from __future__ import annotations

import numpy as np

from ..config import Settings
from ..data import MarketData
from ..schemas import Composite, Light, TrendPoint
from . import margin_institutional as mi
from . import per_deviation as pe
from . import volatility as vo
from .utils import clamp, composite_light

_LABELS: dict[Light, str] = {"green": "風險低", "yellow": "留意", "red": "高風險"}

_HINTS: dict[Light, str] = {
    "green": "目前綜合前兆偏低；歷史上此區間，多按原訂計畫執行較常見（僅供觀測，非投資建議）。",
    "yellow": "部分前兆轉強；歷史上此區間，留意整體倉位、預留現金較常見（僅供觀測，非投資建議）。",
    "red": "多項前兆同時偏高；歷史上此風險區間，提高現金水位、避免使用融資較常見（僅供觀測，非投資建議）。",
}


def _normalized_weights(s: Settings) -> tuple[float, float, float]:
    w = s.weights
    total = w.margin_institutional + w.per + w.volatility
    if total == 0:
        return (1 / 3, 1 / 3, 1 / 3)
    return (w.margin_institutional / total, w.per / total, w.volatility / total)


def _weighted(mi_s: float, per_s: float, vol_s: float,
              wts: tuple[float, float, float]) -> float:
    return clamp(mi_s * wts[0] + per_s * wts[1] + vol_s * wts[2])


def compute_trend(data: MarketData, s: Settings) -> list[TrendPoint]:
    margin = np.array(data.margin.values, dtype=float)
    inst = np.array(data.institutional.values, dtype=float)
    per = np.array(data.per.values, dtype=float)
    vix = np.array(data.vix.values, dtype=float)
    dates = data.margin.dates
    wts = _normalized_weights(s)
    win = s.windows

    n_days = min(win.composite_trend_days, len(margin), len(per), len(vix))
    points: list[TrendPoint] = []
    for j in range(n_days - 1, -1, -1):
        m = margin[: len(margin) - j]
        i = inst[: len(inst) - j]
        p = per[: len(per) - j]
        v = vix[: len(vix) - j]
        score = _weighted(
            mi.subscore(m, i, win),
            pe.subscore(p, win),
            vo.subscore(v, win),
            wts,
        )
        idx = len(dates) - 1 - j
        points.append(TrendPoint(date=dates[idx], score=round(score, 1)))
    return points


def evaluate(data: MarketData, s: Settings,
             mi_score: float, per_score: float, vol_score: float) -> Composite:
    wts = _normalized_weights(s)
    score = _weighted(mi_score, per_score, vol_score, wts)
    light = composite_light(score, s.thresholds.composite_yellow, s.thresholds.composite_red)
    return Composite(
        score=round(score, 1),
        light=light,
        label=_LABELS[light],
        hint=_HINTS[light],
        trend=compute_trend(data, s),
    )
