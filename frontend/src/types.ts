// 與後端 app/schemas.py 對齊
export type Light = "green" | "yellow" | "red";

export interface TrendPoint {
  date: string;
  score: number;
}

export interface MarginPoint {
  date: string;
  margin: number;
  inst_cum: number;
}

export interface PerPoint {
  date: string;
  per: number;
  mean: number;
  upper1: number;
  lower1: number;
  upper2: number;
  lower2: number;
}

export interface VixPoint {
  date: string;
  vix: number;
  p10: number;
  p25: number;
}

export interface MarginSignal {
  light: Light;
  score: number;
  divergence: number;
  margin_high: boolean;
  inst_selling: boolean;
  margin_latest: number;
  inst_cum_latest: number;
  series: MarginPoint[];
}

export interface PerSignal {
  light: Light;
  score: number;
  current: number;
  mean: number;
  sigma: number;
  pctile: number;
  series: PerPoint[];
}

export interface VolatilitySignal {
  light: Light;
  score: number;
  current: number;
  pctile: number;
  is_mock: boolean;
  series: VixPoint[];
}

export interface Composite {
  score: number;
  light: Light;
  label: string;
  hint: string;
  trend: TrendPoint[];
}

// ── Phase 3：美股對照指標 ───────────────────────────────
export interface UsPoint {
  date: string;
  value: number;
}

export interface UsIndicator {
  name: string;
  light: Light;
  current: number;
  pctile: number;
  score: number;
  unit: string;
  hint: string;
  series: UsPoint[];
}

export interface UsReferenceResponse {
  source: string;
  is_mock: boolean;
  indicators: UsIndicator[];
}

// ── Phase 3：歷史回測 ───────────────────────────────────
export interface BacktestPoint {
  date: string;
  score: number;
  index: number;
  forward_return: number;
}

export interface BacktestBucket {
  light: Light;
  label: string;
  count: number;
  avg_forward_return: number;
}

export interface BacktestResponse {
  data_source: string;
  is_mock: boolean;
  horizon: number;
  correlation: number;
  buckets: BacktestBucket[];
  points: BacktestPoint[];
}

export interface RiskResponse {
  updated_at: string;
  data_source: string;
  composite: Composite;
  signals: {
    margin_institutional: MarginSignal;
    per: PerSignal;
    volatility: VolatilitySignal;
  };
  disclaimer: string;
}
