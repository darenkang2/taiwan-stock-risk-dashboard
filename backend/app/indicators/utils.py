"""共用統計小工具（numpy）。"""
from __future__ import annotations

import numpy as np

from ..schemas import Light


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, x)))


def zscore(history: np.ndarray, value: float) -> float:
    """value 相對 history 的標準分數；std 為 0 時回傳 0。"""
    std = float(np.std(history))
    if std == 0:
        return 0.0
    return (value - float(np.mean(history))) / std


def percentile_rank(history: np.ndarray, value: float) -> float:
    """value 在 history 中的百分位 (0–100)：history 中 ≤ value 的比例。"""
    n = history.size
    if n == 0:
        return 50.0
    return float(np.count_nonzero(history <= value)) / n * 100.0


def rolling_sum(arr: np.ndarray, window: int) -> np.ndarray:
    """長度為 len(arr)-window+1 的滾動和。"""
    if arr.size < window:
        return np.array([float(arr.sum())])
    cs = np.cumsum(np.insert(arr, 0, 0.0))
    return cs[window:] - cs[:-window]


def composite_light(score: float, yellow: float, red: float) -> Light:
    if score >= red:
        return "red"
    if score >= yellow:
        return "yellow"
    return "green"
