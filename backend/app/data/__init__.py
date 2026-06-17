"""資料層：統一以 MarketData 提供四條時間序列，供 indicators 計算。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Series:
    """單一指標時間序列。dates 與 values 等長、依日期遞增。"""
    dates: list[str]
    values: list[float]

    def __post_init__(self) -> None:
        if len(self.dates) != len(self.values):
            raise ValueError("dates 與 values 長度不一致")

    def __len__(self) -> int:
        return len(self.values)


@dataclass
class MarketData:
    margin: Series          # 整體市場融資餘額
    institutional: Series   # 整體三大法人單日淨買賣超
    per: Series             # 大盤本益比（或代理）
    vix: Series             # 台指波動率（MVP 以 mock 佔位）
    index: Series           # 加權指數收盤（回測對照後續走勢用）
    source: str             # finmind | mock


@dataclass
class UsReference:
    """美股對照指標（國際對照，可選）。每條序列遞增。"""
    vix: Series             # ^VIX
    cape: Series            # Shiller CAPE
    buffett: Series         # 巴菲特指標＝總市值/GDP（%）
    source: str             # mock | live

