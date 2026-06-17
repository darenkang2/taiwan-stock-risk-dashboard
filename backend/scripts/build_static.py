"""每日靜態資料產生器：把所有 API 輸出寫成 JSON，供純前端（GitHub Pages）讀取。

架構：本專案線上版為「靜態 JSON + GitHub Actions 每日 cron」，不長駐後端。
  每日 workflow 執行本腳本（帶 FINMIND_TOKEN）→ 產出 frontend/public/data/*.json
  → 前端 build → 部署 Pages。前端優先讀這些 JSON，讀不到才 fallback API / 內建 mock。

輸出檔（frontend/public/data/）：
  risk.json | picks.json | us-reference.json | backtest.json | config.json | meta.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# 讓 `python scripts/build_static.py` 能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings, resolve_data_source  # noqa: E402
from app.data.provider import get_us_reference  # noqa: E402
from app.indicators import us_reference  # noqa: E402
from app.services import backtest, picks_service, risk_service  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "data"


def _write(name: str, payload) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    if hasattr(payload, "model_dump_json"):
        path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ {name}")


def main() -> None:
    print(f"建立靜態資料 → {OUT_DIR}（來源：{resolve_data_source(settings)}）")

    risk = risk_service.refresh(settings)
    _write("risk.json", risk)

    picks = picks_service.refresh(settings)
    _write("picks.json", picks)

    ref = get_us_reference(settings)
    _write("us-reference.json",
           us_reference.evaluate(ref, settings.windows, settings.thresholds))

    _write("backtest.json", backtest.run(settings, horizon=20))

    _write("config.json", {
        "windows": settings.windows.__dict__,
        "thresholds": settings.thresholds.__dict__,
        "weights": settings.weights.__dict__,
        "tax": settings.tax.__dict__,
        "position": settings.position.__dict__,
        "etf": settings.etf.__dict__,
        "strategy": settings.strategy.__dict__,
    })

    _write("meta.json", {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "data_source": picks.data_source,
        "market_risk_light": picks.market_risk_light,
        "universe_size": len(picks.universe),
    })

    print("完成。")


if __name__ == "__main__":
    main()
