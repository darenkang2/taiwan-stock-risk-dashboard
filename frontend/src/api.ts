import type {
  BacktestResponse,
  RiskResponse,
  UsReferenceResponse,
} from "./types";
import { mockRisk, mockUsReference, mockBacktest } from "./mockData";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface RiskResult {
  data: RiskResponse;
  usedFallback: boolean; // true 表示後端不可用，改用內建假資料
}

export async function fetchRisk(): Promise<RiskResult> {
  try {
    const resp = await fetch(`${API_BASE}/api/risk`, {
      signal: AbortSignal.timeout(8000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = (await resp.json()) as RiskResponse;
    return { data, usedFallback: false };
  } catch {
    // 後端未啟動或網路問題 → 前端用內建假資料跑起來
    return { data: mockRisk, usedFallback: true };
  }
}

export async function refreshRisk(): Promise<RiskResult> {
  try {
    const resp = await fetch(`${API_BASE}/api/refresh`, {
      method: "POST",
      signal: AbortSignal.timeout(15000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = (await resp.json()) as RiskResponse;
    return { data, usedFallback: false };
  } catch {
    return { data: mockRisk, usedFallback: true };
  }
}

export async function fetchUsReference(): Promise<UsReferenceResponse> {
  try {
    const resp = await fetch(`${API_BASE}/api/us-reference`, {
      signal: AbortSignal.timeout(8000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return (await resp.json()) as UsReferenceResponse;
  } catch {
    return mockUsReference;
  }
}

export async function fetchBacktest(horizon = 20): Promise<BacktestResponse> {
  try {
    const resp = await fetch(`${API_BASE}/api/backtest?horizon=${horizon}`, {
      signal: AbortSignal.timeout(12000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return (await resp.json()) as BacktestResponse;
  } catch {
    return mockBacktest;
  }
}
