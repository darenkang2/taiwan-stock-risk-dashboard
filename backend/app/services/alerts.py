"""Phase 3 — 警示推播（Telegram + Email），沿用既有 pipeline 概念。
未設定對應 token / SMTP 時為 no-op，僅記錄 log。

推播規則（PRD）：
  - 任一前兆首次轉 🔴 → 立即推播
  - 綜合風險分數突破門檻 → 推播
  - 每週一早上推一份「本週風險摘要」
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from ..config import Settings
from ..schemas import RiskResponse

logger = logging.getLogger(__name__)

_LIGHT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


def _send_telegram(settings: Settings, text: str) -> None:
    a = settings.alerts
    if not (a.telegram_bot_token and a.telegram_chat_id):
        logger.info("[alert] (未設定 Telegram，略過) %s", text.splitlines()[0])
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{a.telegram_bot_token}/sendMessage",
            json={"chat_id": a.telegram_chat_id, "text": text},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Telegram 推播失敗：%s", exc)


def _send_email(settings: Settings, subject: str, body: str) -> None:
    a = settings.alerts
    if not (a.smtp_host and a.email_from and a.email_to):
        logger.info("[alert] (未設定 SMTP，略過 Email) %s", subject)
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = a.email_from
        msg["To"] = a.email_to
        with smtplib.SMTP(a.smtp_host, a.smtp_port, timeout=20) as srv:
            srv.starttls()
            if a.smtp_user:
                srv.login(a.smtp_user, a.smtp_password)
            srv.sendmail(a.email_from, [e.strip() for e in a.email_to.split(",")], msg.as_string())
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Email 推播失敗：%s", exc)


def _dispatch(settings: Settings, subject: str, body: str) -> None:
    _send_telegram(settings, f"{subject}\n{body}".strip())
    _send_email(settings, subject, body)


def maybe_alert(settings: Settings, current: RiskResponse,
                previous: RiskResponse | None) -> None:
    """前兆轉紅 / 綜合分數突破門檻時即時推播。"""
    lines: list[str] = []
    c = current.composite

    if c.score >= settings.alerts.composite_alert_threshold and (
        previous is None or previous.composite.score < settings.alerts.composite_alert_threshold
    ):
        lines.append(f"⚠️ 綜合頂部風險分數突破門檻：{c.score}（{c.label}）")

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
            lines.append(f"🔴 前兆轉紅燈：{label}")

    if lines:
        _dispatch(settings, "台股頂部風險｜即時警示", "\n".join(lines))


def build_weekly_summary(current: RiskResponse) -> str:
    c = current.composite
    s = current.signals
    return (
        f"本週風險摘要\n"
        f"綜合風險分數：{c.score}（{c.label}）\n"
        f"・融資×法人背離 {_LIGHT_EMOJI[s.margin_institutional.light]}（{s.margin_institutional.score}）\n"
        f"・本益比偏離 {_LIGHT_EMOJI[s.per.light]}（{s.per.score}）\n"
        f"・波動率極低 {_LIGHT_EMOJI[s.volatility.light]}（{s.volatility.score}）\n"
        f"資料來源：{current.data_source}\n"
        f"（僅供觀測，非投資建議）"
    )


def send_weekly_summary(settings: Settings, current: RiskResponse) -> None:
    _dispatch(settings, "台股頂部風險｜本週摘要", build_weekly_summary(current))
