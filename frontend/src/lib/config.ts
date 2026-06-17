// 平台設定（門檻 / 稅率等）— 單一真實來源為後端 config.py，
// 透過 /api/config 取得；後端不可用時用以下預設值（與後端保持一致）。
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface PlatformConfig {
  tax: {
    supplementary_premium_rate: number; // 二代健保補充保費費率 2.11%
    supplementary_premium_threshold: number; // 單次起扣門檻 20,000
    supplementary_premium_cap: number; // 單次計費上限 10,000,000
    note: string;
  };
  position: {
    stress_test_drop: number; // -60% 壓力測試
    emergency_fund_months_min: number; // 3
    emergency_fund_months_max: number; // 6
  };
  etf: {
    discount_alert_threshold: number; // 折價提示門檻 %（預設 1）
  };
}

export const DEFAULT_CONFIG: PlatformConfig = {
  tax: {
    supplementary_premium_rate: 0.0211,
    supplementary_premium_threshold: 20000,
    supplementary_premium_cap: 10000000,
    note: "2026 現制；改年度結算最快 2027，目前暫緩，請定期確認最新法規。",
  },
  position: {
    stress_test_drop: 0.6,
    emergency_fund_months_min: 3,
    emergency_fund_months_max: 6,
  },
  etf: { discount_alert_threshold: 1.0 },
};

export async function fetchConfig(): Promise<PlatformConfig> {
  try {
    const resp = await fetch(`${API_BASE}/api/config`, {
      signal: AbortSignal.timeout(8000),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return {
      tax: data.tax ?? DEFAULT_CONFIG.tax,
      position: data.position ?? DEFAULT_CONFIG.position,
      etf: data.etf ?? DEFAULT_CONFIG.etf,
    };
  } catch {
    return DEFAULT_CONFIG;
  }
}
