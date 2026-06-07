# 台股頂部風險儀表板（Taiwan Stock Top-Risk Dashboard）

把影片《台股 43500 點…這 3 個崩盤前兆》的**「頂部風險辨識 ＋ 倉位管理」防禦框架**，
變成可每日觀測的 Web 工具。

> **定位**：風險「觀測 / 提醒」工具，**不做自動下單、不給買賣建議**。
> 一切輸出皆為資訊呈現，由使用者自行判斷。
>
> 與既有「布林通道 / MA20 / MA60」進場系統的分工：進場系統回答 *WHAT / WHEN to buy*，
> 本儀表板回答 *HOW MUCH to hold*（整體市場風險水位、要不要降倉、能不能用融資）。

## 目前狀態：MVP（模組 A + 模組 B）

- **模組 A — 三大前兆監測**（每個輸出 🟢/🟡/🔴 燈號 + 0–100 子分數 + 近一年趨勢圖）
  1. **融資 × 法人背離**：融資餘額創 60 日新高 **且** 法人近 10 日累計淨賣超 → 🔴
  2. **本益比偏離歷史均值**：近 10 年 P/E 百分位 / σ 偏離（>+1σ 或前 20% → 🟡；>+2σ 或前 5% → 🔴）
  3. **波動率極低（反直覺）**：VIX 落在近一年最低 10% → 🔴；最低 10–25% → 🟡
- **模組 B — 綜合風險溫度計**：三子分數加權合成 0–100，Apple 風半圓儀表 + 近 90 日趨勢線。

> 規劃中（Phase 2）：模組 C 倉位四鐵律、模組 D 兩大隱形坑計算機。
> Phase 3：美股對照、Telegram/Email 警示、風險分數歷史回測。

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
| GET    | `/api/config`  | 目前採用的門檻 / 視窗 / 權重   |

### 前端

```bash
cd frontend
npm install
cp .env.example .env          # 可選：設定 VITE_API_BASE（預設 http://localhost:8000）
npm run dev                   # http://localhost:5173
```

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
