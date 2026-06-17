"""每交易日 18:00（台北）排程：法人/融資約 15:00–17:00 更新，收盤後跑一次。"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .services import alerts, risk_service

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start(settings: Settings) -> None:
    global _scheduler
    if not settings.scheduler.enabled:
        logger.info("排程未啟用 (SCHEDULER_ENABLED=false)")
        return
    if _scheduler is not None:
        return

    sc = settings.scheduler
    _scheduler = BackgroundScheduler(timezone=sc.timezone)
    _scheduler.add_job(
        lambda: risk_service.refresh(settings),
        CronTrigger(day_of_week="mon-fri", hour=sc.hour, minute=sc.minute,
                    timezone=sc.timezone),
        id="daily_risk_refresh",
        replace_existing=True,
    )

    # 每週一早上推一份「本週風險摘要」
    al = settings.alerts
    if al.weekly_summary_enabled:
        _scheduler.add_job(
            lambda: alerts.send_weekly_summary(settings, risk_service.get_latest(settings)),
            CronTrigger(day_of_week="mon", hour=al.weekly_summary_hour,
                        minute=al.weekly_summary_minute, timezone=sc.timezone),
            id="weekly_summary",
            replace_existing=True,
        )

    _scheduler.start()
    logger.info("排程已啟動：每交易日 %02d:%02d (%s) 更新風險分數；每週一 %02d:%02d 推風險摘要",
                sc.hour, sc.minute, sc.timezone, al.weekly_summary_hour, al.weekly_summary_minute)


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
