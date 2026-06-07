import { useEffect, useState } from "react";

// 倉位檢核 / 計算機輸入狀態存在前端即可（不需登入；跨裝置同步可日後接 Supabase）。
export function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw !== null ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* 忽略寫入失敗（如隱私模式） */
    }
  }, [key, value]);

  return [value, setValue] as const;
}
