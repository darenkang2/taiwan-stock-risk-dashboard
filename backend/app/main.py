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

from .config import resolve_data_source, settings
from .schemas import ConfigResponse, RiskResponse
from .services import risk_service
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


@app.get("/api/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        windows=settings.windows.__dict__,
        thresholds=settings.thresholds.__dict__,
        weights=settings.weights.__dict__,
    )
