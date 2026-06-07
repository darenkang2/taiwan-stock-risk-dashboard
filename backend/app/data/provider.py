"""資料來源選擇器：依設定回傳 MarketData，FinMind 失敗時 fallback mock。"""
from __future__ import annotations

import logging

from ..config import Settings, resolve_data_source
from . import MarketData
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

    # 台指波動率(VIXTWN) 尚未串接 TAIFEX → 永遠以 mock 佔位 (TODO)
    mock = mock_provider.generate()
    return MarketData(
        margin=margin,
        institutional=institutional,
        per=per,
        vix=mock.vix,
        source="finmind",
    )
