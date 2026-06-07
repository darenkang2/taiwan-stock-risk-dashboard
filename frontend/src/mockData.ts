// 前端內建假資料：後端未啟動 / fetch 失敗時的 fallback，
// 讓前端可獨立跑起來（PRD：前端先用假資料跑起來，再接後端）。
// 情境刻意對應「多頭末段」：融資創高、法人轉賣、本益比偏高、波動率極低。
import type {
  MarginPoint,
  PerPoint,
  RiskResponse,
  TrendPoint,
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
