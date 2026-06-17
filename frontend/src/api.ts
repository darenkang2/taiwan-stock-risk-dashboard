import type {
  BacktestResponse,
  PicksResponse,
  RiskResponse,
  UsReferenceResponse,
} from "./types";
import {
  mockRisk,
  mockUsReference,
  mockBacktest,
  mockPicks,
} from "./mockData";

// 線上版為「靜態 JSON（GitHub Actions 每日產生）」；本機開發可接 FastAPI。
// 取得策略：① 先讀靜態 JSON（public/data/*.json）② 後端 API ③ 內建 mock。
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const DATA_BASE = `${import.meta.env.BASE_URL}data`;

async function fetchJson<T>(url: string, timeout: number): Promise<T> {
  const resp = await fetch(url, { signal: AbortSignal.timeout(timeout) });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return (await resp.json()) as T;
}

/** 先靜態 JSON、再後端 API，皆失敗則回傳 mock。 */
async function loadWithFallback<T>(
  file: string,
  apiPath: string,
  mock: T,
  timeout = 8000,
): Promise<{ data: T; usedFallback: boolean }> {
  try {
    return { data: await fetchJson<T>(`${DATA_BASE}/${file}`, timeout), usedFallback: false };
  } catch {
    /* 靜態 JSON 不存在（本機開發）→ 試後端 */
  }
  try {
    return { data: await fetchJson<T>(`${API_BASE}${apiPath}`, timeout), usedFallback: false };
  } catch {
    return { data: mock, usedFallback: true };
  }
}

export interface RiskResult {
  data: RiskResponse;
  usedFallback: boolean;
}

export async function fetchRisk(): Promise<RiskResult> {
  return loadWithFallback<RiskResponse>("risk.json", "/api/risk", mockRisk);
}

export async function refreshRisk(): Promise<RiskResult> {
  // 靜態模式無即時重算；先試後端 /api/refresh，失敗則退回讀取流程。
  try {
    const resp = await fetch(`${API_BASE}/api/refresh`, {
      method: "POST",
      signal: AbortSignal.timeout(15000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return { data: (await resp.json()) as RiskResponse, usedFallback: false };
  } catch {
    return fetchRisk();
  }
}

export async function fetchUsReference(): Promise<UsReferenceResponse> {
  return (
    await loadWithFallback<UsReferenceResponse>(
      "us-reference.json",
      "/api/us-reference",
      mockUsReference,
    )
  ).data;
}

export async function fetchBacktest(horizon = 20): Promise<BacktestResponse> {
  return (
    await loadWithFallback<BacktestResponse>(
      "backtest.json",
      `/api/backtest?horizon=${horizon}`,
      mockBacktest,
      12000,
    )
  ).data;
}

export interface PicksResult {
  data: PicksResponse;
  usedFallback: boolean;
}

export async function fetchPicks(): Promise<PicksResult> {
  return loadWithFallback<PicksResponse>("picks.json", "/api/picks", mockPicks, 10000);
}
