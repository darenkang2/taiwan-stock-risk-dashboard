// 前端內建假資料：後端未啟動 / fetch 失敗時的 fallback，
// 讓前端可獨立跑起來（PRD：前端先用假資料跑起來，再接後端）。
// 情境刻意對應「多頭末段」：融資創高、法人轉賣、本益比偏高、波動率極低。
import type {
  BacktestResponse,
  MarginPoint,
  PerPoint,
  PicksResponse,
  RiskResponse,
  StockPick,
  TrendPoint,
  UsReferenceResponse,
  VixPoint,
} from "./types";

const N = 120;

function dates(n: number): string[] {
  const out: string[] = [];
  const d = new Date(2026, 5, 7); // 2026/06/07
  while (out.length < n) {
    const day = d.getDay();
    if (day !== 0 && day !== 6) out.unshift(d.toISOString().slice(0, 10));
    d.setDate(d.getDate() - 1);
  }
  return out;
}

const ds = dates(N);
const noise = (i: number, amp: number) =>
  (Math.sin(i * 12.9898) * 43758.5453 % 1) * amp - amp / 2;

const marginSeries: MarginPoint[] = ds.map((date, i) => {
  const ramp = i > N - 25 ? ((i - (N - 25)) / 25) * 140 : 0;
  return {
    date,
    margin: Math.round((2400 + 1.2 * i + 30 * Math.sin(i / 60) + ramp + noise(i, 10)) * 10) / 10,
    inst_cum: Math.round((i > N - 12 ? -((i - (N - 12)) / 12) * 600 : noise(i, 120)) * 10) / 10,
  };
});

const perMean = 16.2;
const perStd = 1.4;
const perSeries: PerPoint[] = ds.map((date, i) => {
  const ramp = i > N - 60 ? ((i - (N - 60)) / 60) * 6 : 0;
  return {
    date,
    per: Math.round((14 + 0.01 * i + ramp + noise(i, 0.8)) * 100) / 100,
    mean: perMean,
    upper1: perMean + perStd,
    lower1: perMean - perStd,
    upper2: perMean + 2 * perStd,
    lower2: perMean - 2 * perStd,
  };
});

const vixSeries: VixPoint[] = ds.map((date, i) => {
  const drop = i > N - 30 ? ((i - (N - 30)) / 30) * 12 : 0;
  return {
    date,
    vix: Math.round(Math.max(6, 20 + 3 * Math.sin(i / 40) - drop + noise(i, 1.5)) * 100) / 100,
    p10: 9.5,
    p25: 13.0,
  };
});

const trend: TrendPoint[] = ds.slice(-90).map((date, i) => ({
  date,
  score: Math.round((55 + (i / 90) * 40 + noise(i, 6)) * 10) / 10,
}));

export const mockRisk: RiskResponse = {
  updated_at: new Date(2026, 5, 7, 18, 0).toISOString(),
  data_source: "mock",
  composite: {
    score: 99.2,
    light: "red",
    label: "高風險",
    hint: "多項前兆同時偏高；歷史上此風險區間，提高現金水位、避免使用融資較常見（僅供觀測，非投資建議）。",
    trend,
  },
  signals: {
    margin_institutional: {
      light: "red",
      score: 100,
      divergence: 10.87,
      margin_high: true,
      inst_selling: true,
      margin_latest: marginSeries[N - 1].margin,
      inst_cum_latest: marginSeries[N - 1].inst_cum,
      series: marginSeries,
    },
    per: {
      light: "red",
      score: 100,
      current: perSeries[N - 1].per,
      mean: perMean,
      sigma: 3.98,
      pctile: 100,
      series: perSeries,
    },
    volatility: {
      light: "red",
      score: 99.2,
      current: vixSeries[N - 1].vix,
      pctile: 0.8,
      is_mock: true,
      series: vixSeries,
    },
  },
  disclaimer:
    "本工具僅為個人風險觀測用途，非投資建議。所有門檻為影片觀點之量化詮釋，非保證有效。",
};

// Phase 3 — 美股對照指標 fallback
const usSeries = (base: number, slope: number, end: number) =>
  ds.slice(-90).map((date, i, a) => ({
    date,
    value: Math.round((base + slope * i + (i / a.length) * end + noise(i, 1)) * 100) / 100,
  }));

export const mockUsReference: UsReferenceResponse = {
  source: "mock",
  is_mock: true,
  indicators: [
    { name: "美股 VIX", light: "red", current: 9.79, pctile: 0.4, score: 99.6, unit: "", hint: "低波動＝市場過度樂觀（反直覺）", series: usSeries(16, 0, -6) },
    { name: "Shiller CAPE", light: "yellow", current: 37.38, pctile: 93.5, score: 93.5, unit: "倍", hint: "週期調整本益比，越高越貴", series: usSeries(32, 0.05, 0) },
    { name: "巴菲特指標", light: "red", current: 195.1, pctile: 96.5, score: 96.5, unit: "%", hint: "股市總市值 / GDP，越高越貴", series: usSeries(180, 0.15, 0) },
  ],
};

// Phase 3 — 歷史回測 fallback
export const mockBacktest: BacktestResponse = {
  data_source: "mock",
  is_mock: true,
  horizon: 20,
  correlation: -0.46,
  buckets: [
    { light: "green", label: "風險低 (0–40)", count: 29, avg_forward_return: 5.1 },
    { light: "yellow", label: "留意 (40–70)", count: 166, avg_forward_return: 3.93 },
    { light: "red", label: "高風險 (70–100)", count: 185, avg_forward_return: 1.2 },
  ],
  points: trend.map((p, i) => ({
    date: p.date,
    score: p.score,
    index: 18000 + i * 12 + noise(i, 80),
    forward_return: Math.round((6 - (p.score / 100) * 7 + noise(i, 3)) * 100) / 100,
  })),
};

// 模組 E — 每日選股 fallback（少量代表，涵蓋三風格 + 風險警示）
const mkPick = (p: Partial<StockPick> & Pick<StockPick, "ticker" | "name" | "market">): StockPick => ({
  price: 100, change_pct: 0, score: 60,
  scores: { value: 50, momentum: 50, dividend: 50 },
  top_style: "value", risk_light: "green", tags: [], rationale: "",
  per: null, pb: null, dividend_yield: null, rsi: 50, vol_annual: 25,
  ret_3m: 0, ma_state: "", below_high_pct: 0, is_mock: true, ...p,
});

const mockTop: StockPick[] = [
  mkPick({ ticker: "2882", name: "國泰金", market: "tw", price: 68.5, change_pct: 0.7, score: 78.4, scores: { value: 62, momentum: 71, dividend: 92 }, top_style: "dividend", tags: ["高殖利率", "低波動", "逼近52週高"], per: 12.1, pb: 1.2, dividend_yield: 5.6, rsi: 58, vol_annual: 16.2, ret_3m: 8.4, ma_state: "多頭排列（站上所有均線）", below_high_pct: 1.2, rationale: "主要符合「存股/防禦」：殖利率較高且波動較低，符合穩健存股條件。" }),
  mkPick({ ticker: "MRK", name: "Merck", market: "us", price: 131.2, change_pct: -0.3, score: 76.0, scores: { value: 68, momentum: 64, dividend: 80 }, top_style: "dividend", tags: ["高殖利率", "低波動"], per: 14.8, pb: 5.1, dividend_yield: 3.1, rsi: 49, vol_annual: 18.0, ret_3m: 5.1, ma_state: "中期偏多（站上季線）", below_high_pct: 4.0, rationale: "主要符合「存股/防禦」：殖利率較高且波動較低，符合穩健存股條件。" }),
  mkPick({ ticker: "2330", name: "台積電", market: "tw", price: 1010, change_pct: 1.1, score: 74.5, scores: { value: 55, momentum: 88, dividend: 48 }, top_style: "momentum", tags: ["多頭排列", "逼近52週高", "強勢動能"], per: 22.4, pb: 6.8, dividend_yield: 1.6, rsi: 64, vol_annual: 27.5, ret_3m: 24.0, ma_state: "多頭排列（站上所有均線）", below_high_pct: 0.8, rationale: "主要符合「動能/趨勢」：均線多頭、近期走勢強勢且貼近高點，符合順勢條件。" }),
  mkPick({ ticker: "2002", name: "中鋼", market: "tw", price: 22.3, change_pct: -1.2, score: 70.2, scores: { value: 86, momentum: 41, dividend: 62 }, top_style: "value", tags: ["超賣", "低本益比", "跌破季線"], per: 9.2, pb: 0.9, dividend_yield: 4.4, rsi: 31, vol_annual: 22.0, ret_3m: -9.5, ma_state: "中期偏弱（跌破季線）", below_high_pct: 18.0, rationale: "主要符合「價值/均值回歸」：本益比與股價位階偏低、出現超賣，符合逢低布局條件。" }),
];

const mockWarnings: StockPick[] = [
  mkPick({ ticker: "NVDA", name: "NVIDIA", market: "us", price: 142.5, change_pct: 2.6, score: 58.0, scores: { value: 18, momentum: 95, dividend: 30 }, top_style: "momentum", risk_light: "red", tags: ["過熱", "多頭排列", "本益比偏高", "強勢動能"], per: 52.0, pb: 18.0, dividend_yield: 0.03, rsi: 84, vol_annual: 42.0, ret_3m: 38.0, ma_state: "多頭排列（站上所有均線）", below_high_pct: 0.3, rationale: "主要符合「動能/趨勢」：均線多頭、近期走勢強勢且貼近高點，符合順勢條件。（注意：目前大盤頂部風險偏高，留意整體系統性風險。）" }),
  mkPick({ ticker: "1216", name: "統一", market: "tw", price: 88.4, change_pct: 1.8, score: 55.0, scores: { value: 22, momentum: 86, dividend: 40 }, top_style: "momentum", risk_light: "red", tags: ["過熱", "本益比偏高", "逼近52週高"], per: 38.0, pb: 4.2, dividend_yield: 2.1, rsi: 79, vol_annual: 24.0, ret_3m: 22.0, ma_state: "多頭排列（站上所有均線）", below_high_pct: 0.5, rationale: "主要符合「動能/趨勢」：均線多頭、近期走勢強勢且貼近高點，符合順勢條件。（注意：目前大盤頂部風險偏高，留意整體系統性風險。）" }),
];

export const mockPicks: PicksResponse = {
  updated_at: "2026-06-07T10:00:00+00:00",
  data_source: "mock",
  market_risk_light: "red",
  style_weights: { value: 0.3333, momentum: 0.3333, dividend: 0.3333 },
  top: mockTop,
  warnings: mockWarnings,
  universe: [...mockTop, ...mockWarnings],
  disclaimer:
    "本清單僅為「符合所選策略條件之觀察名單」，非買賣建議；所有門檻為量化詮釋、非保證有效，請自行判斷並注意風險。",
};
