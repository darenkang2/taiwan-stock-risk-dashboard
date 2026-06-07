import type { RiskResponse } from "./types";
import { mockRisk } from "./mockData";

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
