"""集中管理所有可調門檻與常數。

設計原則：影片中的「前兆門檻」皆為作者觀點之量化詮釋，非保證有效。
因此 σ、百分位、天數、權重、稅率全部設成可設定常數，方便日後校準。
可由環境變數覆寫（見各欄位），未設定時使用此處預設值。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw not in (None, "") else default


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else default


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# ──────────────────────────────────────────────────────────────────────────
# 觀測視窗（天數）
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Windows:
    margin_change_days: int = 20      # 融資餘額變化觀測天數
    inst_cumulative_days: int = 10    # 法人累計買賣超天數
    margin_high_days: int = 60        # 融資餘額「創新高」判定視窗
    per_history_years: int = 10       # 本益比歷史均值參考年數
    vix_history_days: int = 252       # 波動率歷史分位參考天數（約一年）
    composite_trend_days: int = 90    # 綜合風險分數趨勢線天數


# ──────────────────────────────────────────────────────────────────────────
# 燈號門檻（皆可調）
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Thresholds:
    # 前兆2：本益比偏離（標準差 / 百分位）
    per_sigma_yellow: float = 1.0     # > +1σ → 🟡
    per_sigma_red: float = 2.0        # > +2σ → 🔴
    per_pctile_yellow: float = 80.0   # 歷史前 20% 高檔 → 🟡
    per_pctile_red: float = 95.0      # 歷史前 5% → 🔴
    # 前兆3：波動率（反直覺，低波動＝高風險）
    vix_pctile_red: float = 10.0      # 近一年最低 10% → 🔴
    vix_pctile_yellow: float = 25.0   # 近一年最低 10–25% → 🟡
    # 模組B：綜合風險分數 0–100
    composite_yellow: float = 40.0    # 40–70 留意
    composite_red: float = 70.0       # 70–100 高風險


# ──────────────────────────────────────────────────────────────────────────
# 模組B：三前兆權重（預設等權，可調；會自動正規化）
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Weights:
    margin_institutional: float = 1 / 3   # 前兆1 融資×法人背離
    per: float = 1 / 3                     # 前兆2 本益比偏離
    volatility: float = 1 / 3              # 前兆3 波動率極低


# ──────────────────────────────────────────────────────────────────────────
# 模組D：稅務 / 二代健保（Phase 2 計算機使用；集中管理、定期更新）
# 2026 現制；改年度結算最快 2027，目前暫緩，請定期確認最新法規。
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TaxConfig:
    supplementary_premium_rate: float = 0.0211      # 二代健保補充保費費率 2.11%
    supplementary_premium_threshold: int = 20_000   # 單次給付起扣門檻
    supplementary_premium_cap: int = 10_000_000     # 單次給付計費上限
    note: str = "2026 現制；改年度結算最快 2027，目前暫緩，請定期確認最新法規。"


# ──────────────────────────────────────────────────────────────────────────
# 模組C：倉位管理四鐵律（Phase 2 互動檢核使用）
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PositionConfig:
    stress_test_drop: float = 0.60          # -60% 壓力測試跌幅
    emergency_fund_months_min: int = 3      # 緊急備用金月數下限
    emergency_fund_months_max: int = 6      # 緊急備用金月數上限


# ──────────────────────────────────────────────────────────────────────────
# 模組D：ETF 折溢價（Phase 2 計算機使用）
# ──────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class EtfConfig:
    discount_alert_threshold: float = 1.0   # 折價超過此 %（門檻可調）即提示


@dataclass(frozen=True)
class FinMindConfig:
    base_url: str = "https://api.finmindtrade.com/api/v4/data"
    token: str = ""
    timeout_seconds: float = 30.0
    # ⚠️ dataset 名稱請以 FinMind 官方文件 (https://finmindtrade.com/) 核對，避免寫死失準。
    dataset_total_margin: str = "TaiwanStockTotalMarginPurchaseShortSale"
    dataset_total_institutional: str = "TaiwanStockTotalInstitutionalInvestors"
    dataset_per: str = "TaiwanStockPER"
    taiex_data_id: str = "TAIEX"  # 大盤本益比代理；FinMind 若無大盤 P/E，Phase 2 改抓 TWSE OpenAPI。


@dataclass(frozen=True)
class SchedulerConfig:
    enabled: bool = True
    timezone: str = "Asia/Taipei"
    hour: int = 18      # 法人/融資約 15:00–17:00 更新，故收盤後 18:00 跑一次
    minute: int = 0


@dataclass(frozen=True)
class AlertConfig:
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    composite_alert_threshold: float = 70.0  # 綜合分數突破即推播
    # Email（SMTP）警示，留空則不寄送
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = ""
    # 每週摘要推播時點（週一早上）
    weekly_summary_enabled: bool = True
    weekly_summary_hour: int = 8
    weekly_summary_minute: int = 0


@dataclass(frozen=True)
class Settings:
    data_source: str = "auto"  # auto | finmind | mock
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    windows: Windows = field(default_factory=Windows)
    thresholds: Thresholds = field(default_factory=Thresholds)
    weights: Weights = field(default_factory=Weights)
    tax: TaxConfig = field(default_factory=TaxConfig)
    position: PositionConfig = field(default_factory=PositionConfig)
    etf: EtfConfig = field(default_factory=EtfConfig)
    finmind: FinMindConfig = field(default_factory=FinMindConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)


def load_settings() -> Settings:
    """從環境變數載入設定，未提供者用預設常數。"""
    token = os.getenv("FINMIND_TOKEN", "").strip()
    data_source = os.getenv("DATA_SOURCE", "auto").strip().lower()
    cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return Settings(
        data_source=data_source,
        cors_origins=[o.strip() for o in cors.split(",") if o.strip()],
        finmind=FinMindConfig(token=token),
        scheduler=SchedulerConfig(
            enabled=_get_bool("SCHEDULER_ENABLED", True),
            timezone=os.getenv("SCHEDULER_TIMEZONE", "Asia/Taipei"),
            hour=_get_int("SCHEDULER_HOUR", 18),
            minute=_get_int("SCHEDULER_MINUTE", 0),
        ),
        alerts=AlertConfig(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            composite_alert_threshold=_get_float("COMPOSITE_ALERT_THRESHOLD", 70.0),
            smtp_host=os.getenv("SMTP_HOST", "").strip(),
            smtp_port=_get_int("SMTP_PORT", 587),
            smtp_user=os.getenv("SMTP_USER", "").strip(),
            smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
            email_from=os.getenv("EMAIL_FROM", "").strip(),
            email_to=os.getenv("EMAIL_TO", "").strip(),
            weekly_summary_enabled=_get_bool("WEEKLY_SUMMARY_ENABLED", True),
            weekly_summary_hour=_get_int("WEEKLY_SUMMARY_HOUR", 8),
            weekly_summary_minute=_get_int("WEEKLY_SUMMARY_MINUTE", 0),
        ),
    )


def resolve_data_source(settings: Settings) -> str:
    """決定實際採用的資料來源：auto 時有 token 用 finmind，否則 mock。"""
    if settings.data_source == "auto":
        return "finmind" if settings.finmind.token else "mock"
    return settings.data_source


settings = load_settings()
