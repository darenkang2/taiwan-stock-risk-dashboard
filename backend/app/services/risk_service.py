"""orchestration：抓取 → 計算燈號 → 快取 → 警示。"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings, settings as default_settings
from ..data.provider import get_market_data
from ..indicators import composite, margin_institutional, per_deviation, volatility
from ..schemas import RiskResponse, Signals
from . import alerts

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[2] / "cache"
CACHE_FILE = CACHE_DIR / "latest.json"

_latest: RiskResponse | None = None


def compute(settings: Settings = default_settings) -> RiskResponse:
    """抓取資料並計算全部燈號與綜合分數。"""
    data = get_market_data(settings)
    w, t = settings.windows, settings.thresholds

    margin_sig = margin_institutional.evaluate(data, w)
    per_sig = per_deviation.evaluate(data, w, t)
    vol_sig = volatility.evaluate(data, w, t, is_mock=True)

    comp = composite.evaluate(data, settings, margin_sig.score, per_sig.score, vol_sig.score)

    return RiskResponse(
        updated_at=datetime.now(timezone.utc).isoformat(),
        data_source=data.source,
        composite=comp,
        signals=Signals(
            margin_institutional=margin_sig, per=per_sig, volatility=vol_sig,
        ),
    )


def refresh(settings: Settings = default_settings) -> RiskResponse:
    """重算、快取、必要時推播。供排程與 /api/refresh 使用。"""
    global _latest
    previous = _latest
    result = compute(settings)
    _latest = result
    _write_cache(result)
    try:
        alerts.maybe_alert(settings, result, previous)
    except Exception as exc:  # 推播失敗不應影響主流程
        logger.warning("警示流程異常：%s", exc)
    logger.info("風險分數已更新：%s（%s, source=%s）",
                result.composite.score, result.composite.label, result.data_source)
    return result


def get_latest(settings: Settings = default_settings) -> RiskResponse:
    """回傳快取；無快取則先載入磁碟，再不行就即時計算。"""
    global _latest
    if _latest is not None:
        return _latest
    cached = _read_cache()
    if cached is not None:
        _latest = cached
        return cached
    return refresh(settings)


def _write_cache(result: RiskResponse) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("寫入快取失敗：%s", exc)


def _read_cache() -> RiskResponse | None:
    try:
        if CACHE_FILE.exists():
            return RiskResponse.model_validate_json(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("讀取快取失敗：%s", exc)
    return None
