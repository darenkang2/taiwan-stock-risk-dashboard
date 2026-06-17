"""FastAPI 入口：台股頂部風險儀表板後端。

Endpoints:
  GET  /api/health   健康檢查
  GET  /api/risk     最新風險分數與三前兆燈號（快取）
  POST /api/refresh  立即重算
  GET  /api/config   目前採用的門檻 / 視窗 / 權重（透明化、方便校準）
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Query

from .config import resolve_data_source, settings
from .data.provider import get_us_reference
from .indicators import us_reference
from .schemas import (
    BacktestResponse,
    ConfigResponse,
    PicksResponse,
    RiskResponse,
    UsReferenceResponse,
)
from .services import backtest, picks_service, risk_service
from . import scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動先算一次，確保 /api/risk 立即有資料
    risk_service.refresh(settings)
    scheduler.start(settings)
    yield
    scheduler.shutdown()


app = FastAPI(title="台股頂部風險儀表板 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "data_source": resolve_data_source(settings)}


@app.get("/api/risk", response_model=RiskResponse)
def get_risk() -> RiskResponse:
    return risk_service.get_latest(settings)


@app.post("/api/refresh", response_model=RiskResponse)
def post_refresh() -> RiskResponse:
    return risk_service.refresh(settings)


@app.get("/api/us-reference", response_model=UsReferenceResponse)
def get_us_reference_endpoint() -> UsReferenceResponse:
    """Phase 3：美股對照指標（^VIX / CAPE / 巴菲特指標）。"""
    ref = get_us_reference(settings)
    return us_reference.evaluate(ref, settings.windows, settings.thresholds)


@app.get("/api/backtest", response_model=BacktestResponse)
def get_backtest(horizon: int = Query(20, ge=5, le=120)) -> BacktestResponse:
    """Phase 3：風險分數歷史回測（對照 N 日後加權指數報酬）。"""
    return backtest.run(settings, horizon=horizon)


@app.get("/api/picks", response_model=PicksResponse)
def get_picks() -> PicksResponse:
    """模組E：每日選股（三風格融合）精選候選 + 風險警示 + 全宇宙評分（快取）。"""
    return picks_service.get_latest(settings)


@app.post("/api/picks/refresh", response_model=PicksResponse)
def post_picks_refresh() -> PicksResponse:
    return picks_service.refresh(settings)


@app.get("/api/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        windows=settings.windows.__dict__,
        thresholds=settings.thresholds.__dict__,
        weights=settings.weights.__dict__,
        tax=settings.tax.__dict__,
        position=settings.position.__dict__,
        etf=settings.etf.__dict__,
        strategy=settings.strategy.__dict__,
    )
