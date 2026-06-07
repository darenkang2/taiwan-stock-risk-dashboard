interface Props {
  label: string;
  value: number | "";
  onChange: (v: number | "") => void;
  suffix?: string;
  placeholder?: string;
}

// Apple 風數字輸入欄
export default function NumberField({ label, value, onChange, suffix, placeholder }: Props) {
  return (
    <label className="block">
      <span className="text-xs text-subtle">{label}</span>
      <div className="mt-1 flex items-center rounded-xl border border-gray-200 bg-canvas px-3 py-2 focus-within:border-ink/30">
        <input
          type="number"
          inputMode="decimal"
          value={value}
          placeholder={placeholder}
          onChange={(e) => {
            const v = e.target.value;
            onChange(v === "" ? "" : Number(v));
          }}
          className="w-full bg-transparent text-base font-medium tabular-nums text-ink outline-none placeholder:text-subtle/50"
        />
        {suffix && <span className="ml-2 shrink-0 text-xs text-subtle">{suffix}</span>}
      </div>
    </label>
  );
}
