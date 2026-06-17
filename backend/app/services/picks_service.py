"""模組 E orchestration：掃描選股宇宙 → 逐檔評分 → 組裝精選 / 警示 / 全宇宙。

大盤頂部風險燈（來自既有 risk_service 綜合分數）會帶入個股風險判斷，
形成「個股策略分數」與「整體系統性風險」分工：分數回答 *選哪些*，
大盤燈提醒 *此刻整體要不要更謹慎*。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings, settings as default_settings
from ..data.stock_provider import get_stock_snapshots
from ..indicators import stock_strategy
from ..schemas import PicksResponse, StockPick
from . import risk_service

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[2] / "cache"
CACHE_FILE = CACHE_DIR / "picks.json"

_latest: PicksResponse | None = None


def compute(settings: Settings = default_settings) -> PicksResponse:
    cfg = settings.strategy
    market_light = _market_light(settings)

    snapshots, source = get_stock_snapshots(settings)
    picks: list[StockPick] = [
        stock_strategy.evaluate(snap, market_light, cfg) for snap in snapshots
    ]

    ranked = sorted(picks, key=lambda p: p.score, reverse=True)
    top = ranked[: cfg.top_n]
    warnings = sorted(
        [p for p in picks if p.risk_light == "red"],
        key=lambda p: p.rsi, reverse=True,
    )[: cfg.max_warnings]

    return PicksResponse(
        updated_at=datetime.now(timezone.utc).isoformat(),
        data_source=source,
        market_risk_light=market_light,
        style_weights=stock_strategy.normalized_weights(cfg),
        top=top,
        warnings=warnings,
        universe=ranked,
    )


def _market_light(settings: Settings):
    try:
        return risk_service.get_latest(settings).composite.light
    except Exception as exc:  # noqa: BLE001 — 大盤燈取得失敗不應中斷選股
        logger.warning("取得大盤風險燈失敗，以 green 代入：%s", exc)
        return "green"


def refresh(settings: Settings = default_settings) -> PicksResponse:
    global _latest
    result = compute(settings)
    _latest = result
    _write_cache(result)
    logger.info("每日選股已更新：top=%d warnings=%d source=%s",
                len(result.top), len(result.warnings), result.data_source)
    return result


def get_latest(settings: Settings = default_settings) -> PicksResponse:
    global _latest
    if _latest is not None:
        return _latest
    cached = _read_cache()
    if cached is not None:
        _latest = cached
        return cached
    return refresh(settings)


def _write_cache(result: PicksResponse) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("寫入選股快取失敗：%s", exc)


def _read_cache() -> PicksResponse | None:
    try:
        if CACHE_FILE.exists():
            return PicksResponse.model_validate_json(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("讀取選股快取失敗：%s", exc)
    return None
