"""Phase 3 — 風險分數歷史回測。

方法：逐日重算綜合風險分數，對照「N 日後加權指數報酬」，
依風險區間（綠/黃/紅）統計後續平均報酬，並計算分數與後續報酬的相關係數，
用以檢視「高風險區間是否對應較弱的後續走勢」。

⚠️ 目前資料為 mock，僅示範方法；歷史關聯不代表未來必然發生。
"""
from __future__ import annotations

import numpy as np

from ..config import Settings
from ..config import settings as default_settings
from ..data.provider import get_market_data
from ..indicators import composite
from ..indicators.utils import composite_light
from ..schemas import BacktestBucket, BacktestPoint, BacktestResponse


def run(settings: Settings = default_settings, horizon: int = 20) -> BacktestResponse:
    data = get_market_data(settings)
    t = settings.thresholds

    # 全期逐日綜合分數
    scores = composite.daily_scores(data, settings, last_n=None)
    score_by_date = {p.date: p.score for p in scores}

    idx_dates = data.index.dates
    idx_vals = np.array(data.index.values, dtype=float)
    pos = {d: i for i, d in enumerate(idx_dates)}

    points: list[BacktestPoint] = []
    bucket_returns: dict[str, list[float]] = {"green": [], "yellow": [], "red": []}

    for p in scores:
        i = pos.get(p.date)
        if i is None or i + horizon >= len(idx_vals):
            continue
        fwd = float(idx_vals[i + horizon] / idx_vals[i] - 1.0) * 100.0
        light = composite_light(p.score, t.composite_yellow, t.composite_red)
        points.append(
            BacktestPoint(date=p.date, score=p.score,
                          index=round(float(idx_vals[i]), 2),
                          forward_return=round(fwd, 2))
        )
        bucket_returns[light].append(fwd)

    buckets = [
        BacktestBucket(
            light=light,  # type: ignore[arg-type]
            label={"green": "風險低 (0–40)", "yellow": "留意 (40–70)", "red": "高風險 (70–100)"}[light],
            count=len(vals),
            avg_forward_return=round(float(np.mean(vals)), 2) if vals else 0.0,
        )
        for light, vals in bucket_returns.items()
    ]

    all_scores = np.array([p.score for p in points])
    all_fwd = np.array([p.forward_return for p in points])
    corr = (
        round(float(np.corrcoef(all_scores, all_fwd)[0, 1]), 3)
        if all_scores.size > 2 and all_scores.std() > 0 and all_fwd.std() > 0
        else 0.0
    )

    return BacktestResponse(
        data_source=data.source,
        is_mock=data.source == "mock",
        horizon=horizon,
        correlation=corr,
        buckets=buckets,
        points=points,
    )
