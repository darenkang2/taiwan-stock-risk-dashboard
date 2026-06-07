"""確定性 mock 資料產生器。

用途：
  1. 未設定 FINMIND_TOKEN 時，讓前後端可立即跑起來（PRD：前端先用假資料跑起來）。
  2. 單元測試的穩定輸入。
  3. 台指波動率(VIXTWN) 在串接 TAIFEX 前，永遠以此佔位（標記 is_mock）。

刻意營造「多頭末段」情境，方便檢視儀表板：
  融資餘額貼近高檔、法人轉為小幅淨賣、本益比偏高、波動率偏低。
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from . import MarketData, Series


def _trading_days(n: int, end: date) -> list[str]:
    """產生 n 個交易日（略過週末）字串，遞增排序，結束於 end。"""
    days: list[str] = []
    d = end
    while len(days) < n:
        if d.weekday() < 5:  # 0=Mon ... 4=Fri
            days.append(d.isoformat())
        d -= timedelta(days=1)
    return list(reversed(days))


def generate(end: date | None = None, seed: int = 20260607) -> MarketData:
    end = end or date.today()
    rng = np.random.default_rng(seed)

    n = 400  # 約一年半交易日，足夠 252 天分位與 90 天趨勢
    dates = _trading_days(n, end)
    t = np.arange(n)

    # 融資餘額：緩步上升 + 末段散戶融資衝高至區間最高（億元）
    margin = 2300 + 1.2 * t + 40 * np.sin(t / 60) + rng.normal(0, 8, n)
    margin[-25:] += np.linspace(0, 140, 25)  # 末段衝高
    margin[-1] = float(margin[-60:].max()) + 8.0  # 確保末日創 60 日新高
    margin = np.maximum(margin, 100)

    # 三大法人單日淨買賣超（億元）：近期轉為持續淨賣（聰明錢悄悄出貨）
    inst = rng.normal(8, 35, n)
    inst[-12:] -= np.linspace(40, 110, 12)  # 近 10 日累計明顯淨賣超

    # 大盤本益比：緩升 + 末段拉到歷史前段高檔（高百分位 / >1σ）
    per = 14.0 + 0.004 * t + rng.normal(0, 0.5, n)
    per[-60:] += np.linspace(0, 6.0, 60)

    # 波動率（VIXTWN 佔位）：近期壓到近一年最低區間（過度樂觀、毫無防備）
    vix = 20 + 3.0 * np.sin(t / 70) + rng.normal(0, 1.2, n)
    vix[-30:] -= np.linspace(0, 12, 30)
    vix = np.maximum(vix, 6)

    return MarketData(
        margin=Series(dates, [round(float(x), 1) for x in margin]),
        institutional=Series(dates, [round(float(x), 1) for x in inst]),
        per=Series(dates, [round(float(x), 2) for x in per]),
        vix=Series(dates, [round(float(x), 2) for x in vix]),
        source="mock",
    )
