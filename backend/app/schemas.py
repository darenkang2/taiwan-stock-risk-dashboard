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


class ConfigResponse(BaseModel):
    windows: dict
    thresholds: dict
    weights: dict
