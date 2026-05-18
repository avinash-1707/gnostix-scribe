"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  label: string;
  placeholder?: string;
  autoComplete?: string;
  minLength?: number;
  required?: boolean;
  id?: string;
};

export function PasswordInput({
  value,
  onChange,
  label,
  placeholder = "••••••••",
  autoComplete = "current-password",
  minLength,
  required = true,
  id,
}: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="flex flex-col gap-2" htmlFor={id}>
      <span className="text-xs uppercase tracking-[0.2em] text-white/40">
        {label}
      </span>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          required={required}
          minLength={minLength}
          autoComplete={autoComplete}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md bg-white/3 border border-white/1 px-3 py-2.5 pr-10 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/3 focus:bg-white/5 transition-colors"
          placeholder={placeholder}
        />
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute right-2 top-1/2 -translate-y-1/2 grid place-items-center h-7 w-7 rounded text-white/40 hover:text-white/80 transition-colors"
        >
          {visible ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>
    </label>
  );
}
