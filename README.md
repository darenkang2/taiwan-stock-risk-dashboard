# 台股頂部風險儀表板（Taiwan Stock Top-Risk Dashboard）

把影片《台股 43500 點…這 3 個崩盤前兆》的**「頂部風險辨識 ＋ 倉位管理」防禦框架**，
變成可每日觀測的 Web 工具。

> **定位**：風險「觀測 / 提醒」工具，**不做自動下單、不給買賣建議**。
> 一切輸出皆為資訊呈現，由使用者自行判斷。
>
> 與既有「布林通道 / MA20 / MA60」進場系統的分工：進場系統回答 *WHAT / WHEN to buy*，
> 本儀表板回答 *HOW MUCH to hold*（整體市場風險水位、要不要降倉、能不能用融資）。

## 目前狀態：模組 A / B / C / D / E 皆已完成

> **線上部署架構**：靜態 JSON + GitHub Actions 每日 cron。
> 每日（美股收盤後）由 workflow 執行 `backend/scripts/build_static.py`
> （FinMind 台股 + yfinance 美股）產出 `frontend/public/data/*.json`，再 build 前端並部署 GitHub Pages。
> **不需長駐後端**；前端優先讀靜態 JSON，讀不到才 fallback 本機 API / 內建 mock。
> 未設定 `FINMIND_TOKEN` 時資料自動以 mock 產生，demo 仍可完整操作。

- **模組 A — 三大前兆監測**（每個輸出 🟢/🟡/🔴 燈號 + 0–100 子分數 + 近一年趨勢圖）
  1. **融資 × 法人背離**：融資餘額創 60 日新高 **且** 法人近 10 日累計淨賣超 → 🔴
  2. **本益比偏離歷史均值**：近 10 年 P/E 百分位 / σ 偏離（>+1σ 或前 20% → 🟡；>+2σ 或前 5% → 🔴）
  3. **波動率極低（反直覺）**：VIX 落在近一年最低 10% → 🔴；最低 10–25% → 🟡
- **模組 B — 綜合風險溫度計**：三子分數加權合成 0–100，Apple 風半圓儀表 + 近 90 日趨勢線。
- **模組 C — 倉位管理四鐵律**（互動檢核，狀態存 localStorage）：閒置資金檢核、-60% 壓力測試、
  融資紅線（與模組 B 綜合燈號連動）、緊急備用金追蹤。
- **模組 D — 兩大隱形坑計算機**：ETF 折溢價監控（MVP 手動輸入 NAV）、
  股利稅＋二代健保補充保費（稅後實際報酬率 vs 帳面殖利率）。
- **Phase 3 — 美股對照指標**：^VIX / Shiller CAPE / 巴菲特指標（國際對照，不併入台股綜合分數；mock 佔位待實接）。
- **Phase 3 — 警示推播**：Telegram + Email（SMTP）；前兆轉 🔴 / 綜合分數突破門檻即時推播，每週一早上推「本週風險摘要」。
- **Phase 3 — 風險分數歷史回測**：逐日重算綜合分數，對照 N 日後加權指數報酬，依風險區間統計平均後續報酬 + 相關係數。
- **模組 E — 每日選股（三風格融合）**：掃描大型權值股（台股 0050/0100＋美股 Nasdaq100/S&P500），
  以**透明、可調**的綜合選股分數融合三種投資風格——
  **價值/均值回歸**（本益比偏低、RSI 超賣、跌深）、
  **動能/趨勢**（均線多頭、近三月強勢、貼近 52 週高）、
  **存股/防禦**（高殖利率、低波動）。
  輸出「每日精選候選」+「風險警示（過熱/偏貴，大盤紅燈時上調）」+ 全宇宙評分（供追蹤清單查詢）。
  每檔附三風格子分數、白話標籤與一句話理由。**定位同全站：符合策略條件之觀察名單，非買賣建議。**
  權重 / 門檻全在 `config.py` 的 `StrategyConfig`，可由環境變數（`STRATEGY_W_VALUE` 等）覆寫。
- **追蹤清單**：自選關注標的，每日同步最新評分；儲存於瀏覽器 localStorage，**不需登入**。

## 架構

```
backend/   Python FastAPI：抓取(FinMind) → 計算燈號 → 快取 → (排程/警示)
frontend/  React + Vite + TypeScript + Tailwind + Recharts（Apple 商務風、繁中）
```

資料流：`FinMind / mock → indicators → /api/risk → React`。
未設定 `FINMIND_TOKEN` 時自動以 **mock 假資料**運行；前端在後端不可用時也會 fallback 內建假資料。

## 快速開始

### 後端

```bash
cd backend
uv venv --python 3.11 .venv && uv pip install -e ".[dev]"
cp .env.example .env          # 可選：填入 FINMIND_TOKEN（不填則用 mock）
.venv/bin/pytest -q           # 跑單元測試
.venv/bin/uvicorn app.main:app --reload --port 8000
```

API：

| Method | Path           | 說明                         |
| ------ | -------------- | ---------------------------- |
| GET    | `/api/health`  | 健康檢查 + 目前資料來源       |
| GET    | `/api/risk`    | 最新風險分數與三前兆燈號（快取） |
| POST   | `/api/refresh` | 立即重算                     |
| GET    | `/api/config`  | 目前採用的門檻 / 視窗 / 權重 / 稅率 |
| GET    | `/api/us-reference` | 美股對照指標（^VIX / CAPE / 巴菲特指標）|
| GET    | `/api/backtest?horizon=20` | 風險分數歷史回測（前瞻 5–120 日）|
| GET    | `/api/picks`   | 模組E：每日選股（精選候選 + 風險警示 + 全宇宙評分，快取）|
| POST   | `/api/picks/refresh` | 立即重掃選股宇宙 |

### 前端

```bash
cd frontend
npm install
cp .env.example .env          # 可選：設定 VITE_API_BASE（預設 http://localhost:8000）
npm run dev                   # http://localhost:5173
```

### 產生靜態資料（線上部署用）

```bash
cd backend
.venv/bin/python scripts/build_static.py   # → frontend/public/data/*.json
```

未設 `FINMIND_TOKEN` 則以 mock 產生；前端在無此 JSON 時會自動 fallback 內建 mock。
GitHub Actions 每日 cron 會自動執行此步驟並部署，無需手動。

## 可調參數（集中管理）

所有門檻皆為「影片觀點之量化詮釋，非保證有效」，因此全部設成可設定常數，方便日後校準：

- 後端 `backend/app/config.py`：觀測視窗（天數）、燈號門檻（σ / 百分位）、三前兆權重、
  稅務 / 二代健保費率（模組 D 用），多數可由環境變數覆寫。
- 透過 `GET /api/config` 可查看目前生效值。

## 資料來源備註

- FinMind dataset 名稱（`TaiwanStockTotalMarginPurchaseShortSale` 等）為**建議對應**，
  上線前請以 [FinMind 官方文件](https://finmindtrade.com/) 核對欄位，避免改名失準。
- **台指波動率(VIXTWN)** 尚未串接 TAIFEX，MVP 以 mock 佔位並標記 `is_mock`（見 `volatility.py` 的 TODO）。
- 大盤本益比以 FinMind `TaiwanStockPER`(TAIEX) 代理；Phase 2 可改抓 TWSE OpenAPI。
- 排程：法人 / 融資約 15:00–17:00 更新，預設**每交易日 18:00（台北）**重算一次。

## 免責

本工具僅為**個人風險觀測用途，非投資建議**。所有門檻為作者影片觀點之量化詮釋，非保證有效。
稅務 / 健保費率屬政策（2026 現制），請於 `config.py` 集中管理並定期更新。
