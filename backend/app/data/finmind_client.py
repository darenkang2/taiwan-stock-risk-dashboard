"""FinMind API 客戶端（v4）。

⚠️ 重要：以下 dataset 名稱與欄位對應為「建議值」，實作上線前請以 FinMind 官方文件
(https://finmindtrade.com/) 核對，避免欄位改名導致失準。

設計：
  - 抓取整體市場融資餘額、整體三大法人買賣超、大盤本益比代理。
  - 任一抓取失敗則拋出 FinMindError，由 provider 決定是否 fallback。
  - 台指波動率(VIXTWN) FinMind 目前無對應 → 不在此抓取，由 provider 以 mock 佔位 (TODO: 串 TAIFEX)。
"""
from __future__ import annotations

from datetime import date, timedelta

import httpx

from ..config import FinMindConfig
from . import Series


class FinMindError(RuntimeError):
    pass


def _fetch(cfg: FinMindConfig, dataset: str, start_date: str,
           data_id: str | None = None) -> list[dict]:
    params: dict[str, str] = {"dataset": dataset, "start_date": start_date}
    if data_id:
        params["data_id"] = data_id
    if cfg.token:
        params["token"] = cfg.token
    try:
        resp = httpx.get(cfg.base_url, params=params, timeout=cfg.timeout_seconds)
        resp.raise_for_status()
    except httpx.HTTPError as exc:  # 含逾時、連線、4xx/5xx
        raise FinMindError(f"FinMind 請求失敗 dataset={dataset}: {exc}") from exc
    payload = resp.json()
    if payload.get("status") != 200 and payload.get("msg") not in (None, "success"):
        raise FinMindError(f"FinMind 回傳異常 dataset={dataset}: {payload.get('msg')}")
    data = payload.get("data") or []
    if not data:
        raise FinMindError(f"FinMind 無資料 dataset={dataset}")
    return data


def _pick(row: dict, candidates: tuple[str, ...]) -> float | None:
    """從多個可能欄位名中取第一個存在且可轉數值者（容忍 FinMind 欄位差異）。"""
    for key in candidates:
        if key in row and row[key] not in (None, ""):
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return None


def _aggregate_by_date(rows: list[dict], value_candidates: tuple[str, ...]) -> Series:
    """將同一日期的多列（如分項法人 / 多市場）加總為單一序列。"""
    by_date: dict[str, float] = {}
    for row in rows:
        d = row.get("date")
        v = _pick(row, value_candidates)
        if d is None or v is None:
            continue
        by_date[d] = by_date.get(d, 0.0) + v
    if not by_date:
        raise FinMindError("FinMind 資料無可用欄位")
    dates = sorted(by_date)
    return Series(dates, [round(by_date[d], 2) for d in dates])


def _start_date(days_back: int) -> str:
    return (date.today() - timedelta(days=days_back)).isoformat()


def fetch_total_margin(cfg: FinMindConfig) -> Series:
    """整體市場融資餘額（取今日餘額類欄位）。"""
    rows = _fetch(cfg, cfg.dataset_total_margin, _start_date(800))
    # 候選欄位：TodayBalance / MarginPurchaseTodayBalance（依官方文件可能不同）
    return _aggregate_by_date(
        rows, ("MarginPurchaseTodayBalance", "TodayBalance", "balance"),
    )


def fetch_total_institutional(cfg: FinMindConfig) -> Series:
    """整體三大法人單日淨買賣超（買進 − 賣出，多市場/分項加總）。"""
    rows = _fetch(cfg, cfg.dataset_total_institutional, _start_date(800))
    by_date: dict[str, float] = {}
    for row in rows:
        d = row.get("date")
        if d is None:
            continue
        net = _pick(row, ("net", "buy_sell"))
        if net is None:
            buy = _pick(row, ("buy",)) or 0.0
            sell = _pick(row, ("sell",)) or 0.0
            net = buy - sell
        by_date[d] = by_date.get(d, 0.0) + net
    if not by_date:
        raise FinMindError("FinMind 法人資料無可用欄位")
    dates = sorted(by_date)
    return Series(dates, [round(by_date[d], 2) for d in dates])


def fetch_market_per(cfg: FinMindConfig) -> Series:
    """大盤本益比代理。

    TODO: FinMind 若無大盤 P/E 欄位，Phase 2 改抓 TWSE OpenAPI
    「發行量加權股價指數本益比」。此處先以 TaiwanStockPER 之 TAIEX 代理嘗試。
    """
    rows = _fetch(cfg, cfg.dataset_per, _start_date(3700), data_id=cfg.taiex_data_id)
    return _aggregate_by_date(rows, ("PER", "per"))
