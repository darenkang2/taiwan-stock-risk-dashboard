"""API 回傳資料結構（Pydantic）。前端 types.ts 與此對齊。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Light = Literal["green", "yellow", "red"]


class TrendPoint(BaseModel):
    date: str
    score: float


class MarginPoint(BaseModel):
    date: str
    margin: float       # 融資餘額
    inst_cum: float     # 法人近 N 日累計買賣超


class PerPoint(BaseModel):
    date: str
    per: float
    mean: float
    upper1: float
    lower1: float
    upper2: float
    lower2: float


class VixPoint(BaseModel):
    date: str
    vix: float
    p10: float          # 近一年最低 10% 分位線
    p25: float          # 近一年最低 25% 分位線


class MarginSignal(BaseModel):
    light: Light
    score: float
    divergence: float       # z(融資20日變化) − z(法人10日累計淨買超)
    margin_high: bool       # 融資餘額創 60 日新高
    inst_selling: bool      # 法人近 10 日累計淨賣超
    margin_latest: float
    inst_cum_latest: float
    series: list[MarginPoint]


class PerSignal(BaseModel):
    light: Light
    score: float
    current: float
    mean: float
    sigma: float            # 偏離標準差數
    pctile: float           # 歷史百分位
    series: list[PerPoint]


class VolatilitySignal(BaseModel):
    light: Light
    score: float
    current: float
    pctile: float           # 近一年分位（低＝高風險）
    is_mock: bool           # TODO: 台指波動率(VIXTWN) 串接 TAIFEX 前以 mock 佔位
    series: list[VixPoint]


class Signals(BaseModel):
    margin_institutional: MarginSignal
    per: PerSignal
    volatility: VolatilitySignal


class Composite(BaseModel):
    score: float
    light: Light
    label: str              # 風險低 / 留意 / 高風險
    hint: str               # 觀測提示（非投資建議）
    trend: list[TrendPoint]


class RiskResponse(BaseModel):
    updated_at: str
    data_source: str        # finmind | mock
    composite: Composite
    signals: Signals
    disclaimer: str = "本工具僅為個人風險觀測用途，非投資建議。所有門檻為影片觀點之量化詮釋，非保證有效。"


# ── Phase 3：美股對照指標 ───────────────────────────────────────────────
class UsPoint(BaseModel):
    date: str
    value: float


class UsIndicator(BaseModel):
    name: str
    light: Light
    current: float
    pctile: float
    score: float
    unit: str
    hint: str
    series: list[UsPoint]


class UsReferenceResponse(BaseModel):
    source: str
    is_mock: bool
    indicators: list[UsIndicator]


# ── Phase 3：風險分數歷史回測 ──────────────────────────────────────────
class BacktestPoint(BaseModel):
    date: str
    score: float
    index: float
    forward_return: float   # N 日後加權指數報酬 (%)


class BacktestBucket(BaseModel):
    light: Light
    label: str
    count: int
    avg_forward_return: float


class BacktestResponse(BaseModel):
    data_source: str
    is_mock: bool
    horizon: int            # 前瞻天數
    correlation: float      # 風險分數 vs 後續報酬 相關係數
    buckets: list[BacktestBucket]
    points: list[BacktestPoint]


class ConfigResponse(BaseModel):
    windows: dict
    thresholds: dict
    weights: dict
    tax: dict          # 模組D：二代健保補充保費費率 / 門檻 / 上限
    position: dict     # 模組C：壓力測試跌幅、緊急備用金月數
    etf: dict          # 模組D：ETF 折價提示門檻
