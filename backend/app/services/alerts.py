"""警示推播（Phase 3 雛形）。沿用既有 Telegram / Email pipeline 的概念，
未設定 token 時為 no-op，僅記錄 log。

推播規則（PRD）：
  - 任一前兆首次轉 🔴 → 立即推播
  - 綜合風險分數突破門檻 → 推播
"""
from __future__ import annotations

import logging

import httpx

from ..config import Settings
from ..schemas import RiskResponse

logger = logging.getLogger(__name__)


def _send_telegram(settings: Settings, text: str) -> None:
    a = settings.alerts
    if not (a.telegram_bot_token and a.telegram_chat_id):
        logger.info("[alert] (未設定 Telegram，略過) %s", text)
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{a.telegram_bot_token}/sendMessage",
            json={"chat_id": a.telegram_chat_id, "text": text},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Telegram 推播失敗：%s", exc)


def maybe_alert(settings: Settings, current: RiskResponse,
                previous: RiskResponse | None) -> None:
    msgs: list[str] = []
    c = current.composite

    if c.score >= settings.alerts.composite_alert_threshold:
        if previous is None or previous.composite.score < settings.alerts.composite_alert_threshold:
            msgs.append(f"⚠️ 綜合頂部風險分數突破門檻：{c.score}（{c.label}）")

    sig = current.signals
    prev_sig = previous.signals if previous else None
    for name, label in (
        ("margin_institutional", "融資×法人背離"),
        ("per", "本益比偏離"),
        ("volatility", "波動率極低"),
    ):
        cur_light = getattr(sig, name).light
        prev_light = getattr(prev_sig, name).light if prev_sig else None
        if cur_light == "red" and prev_light != "red":
            msgs.append(f"🔴 前兆轉紅燈：{label}")

    for m in msgs:
        _send_telegram(settings, m)
