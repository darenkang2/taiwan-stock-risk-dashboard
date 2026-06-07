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
