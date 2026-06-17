import type { Style } from "../types";

export const STYLE_LABEL: Record<Style, string> = {
  value: "價值/均值回歸",
  momentum: "動能/趨勢",
  dividend: "存股/防禦",
};

export const STYLE_SHORT: Record<Style, string> = {
  value: "價值",
  momentum: "動能",
  dividend: "存股",
};

// 三風格代表色（與風險燈色系區隔）
export const STYLE_COLOR: Record<Style, string> = {
  value: "#0A84FF", // 藍
  momentum: "#FF9500", // 橘
  dividend: "#30B0C7", // 青
};
