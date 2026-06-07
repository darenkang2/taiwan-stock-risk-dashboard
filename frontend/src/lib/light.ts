import type { Light } from "../types";

export const LIGHT_COLOR: Record<Light, string> = {
  green: "#34C759",
  yellow: "#FF9F0A",
  red: "#FF3B30",
};

export const LIGHT_LABEL: Record<Light, string> = {
  green: "綠燈",
  yellow: "黃燈",
  red: "紅燈",
};

export const LIGHT_EMOJI: Record<Light, string> = {
  green: "🟢",
  yellow: "🟡",
  red: "🔴",
};

// 卡片左緣強調色帶用的淡背景
export const LIGHT_SOFT_BG: Record<Light, string> = {
  green: "rgba(52,199,89,0.10)",
  yellow: "rgba(255,159,10,0.12)",
  red: "rgba(255,59,48,0.10)",
};
