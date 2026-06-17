import type { ReactNode } from "react";

export function Panel({
  title,
  children,
  className = "",
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl ${className}`}>
      <h2 className="mb-4 text-lg font-semibold text-white">{title}</h2>
      {children}
    </section>
  );
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = "primary",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost";
}) {
  const styles = {
    primary: "bg-indigo-500 hover:bg-indigo-400 text-white",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-100",
    ghost: "bg-transparent hover:bg-slate-800 text-slate-200 border border-slate-700",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-xl px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

export function Select({
  value,
  onChange,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-400"
    >
      {children}
    </select>
  );
}

export function ProgressBar({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  const percent = Math.round(Math.min(100, Math.max(0, value * 100)));

  return (
    <div className="mt-3">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-indigo-300">{label}</span>
        <span className="font-medium text-slate-300">%{percent}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-400 transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

export function TextArea({
  value,
  onChange,
  rows = 8,
  placeholder,
  readOnly = false,
  className = "",
}: {
  value: string;
  onChange?: (value: string) => void;
  rows?: number;
  placeholder?: string;
  readOnly?: boolean;
  className?: string;
}) {
  return (
    <textarea
      value={value}
      readOnly={readOnly}
      rows={rows}
      placeholder={placeholder}
      onChange={(event) => onChange?.(event.target.value)}
      className={`w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-400 ${className}`}
    />
  );
}
