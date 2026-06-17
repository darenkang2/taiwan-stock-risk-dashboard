"""資料來源選擇器：依設定回傳 MarketData，FinMind 失敗時 fallback mock。"""
from __future__ import annotations

import logging

from ..config import Settings, resolve_data_source
from . import MarketData, UsReference
from . import finmind_client as fm
from . import mock_provider

logger = logging.getLogger(__name__)


def get_market_data(settings: Settings) -> MarketData:
    source = resolve_data_source(settings)
    if source == "mock":
        return mock_provider.generate()

    # source == "finmind"
    try:
        cfg = settings.finmind
        margin = fm.fetch_total_margin(cfg)
        institutional = fm.fetch_total_institutional(cfg)
        per = fm.fetch_market_per(cfg)
    except fm.FinMindError as exc:
        logger.warning("FinMind 抓取失敗，fallback mock：%s", exc)
        return mock_provider.generate()

    # 台指波動率(VIXTWN) 與加權指數先以 mock 佔位 (TODO: 串 TAIFEX / FinMind 指數)
    mock = mock_provider.generate()
    return MarketData(
        margin=margin,
        institutional=institutional,
        per=per,
        vix=mock.vix,
        index=mock.index,
        source="finmind",
    )


def get_us_reference(settings: Settings) -> UsReference:
    """美股對照指標（國際對照，可選）。

    TODO: 實接 ^VIX（Yahoo）、Shiller CAPE（multpl.com）、巴菲特指標（FRED）。
    目前一律以 mock 佔位。
    """
    return mock_provider.generate_us_reference()
