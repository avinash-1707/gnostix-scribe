"use client";

import { motion } from "motion/react";

export type StrengthLevel = 0 | 1 | 2 | 3 | 4;

const LABELS: Record<StrengthLevel, string> = {
  0: "Too weak",
  1: "Weak",
  2: "Fair",
  3: "Strong",
  4: "Excellent",
};

const COLORS: Record<StrengthLevel, string> = {
  0: "bg-rose-500/70",
  1: "bg-rose-400/80",
  2: "bg-amber-400/80",
  3: "bg-emerald-400/80",
  4: "bg-emerald-300",
};

export function scorePassword(pw: string): StrengthLevel {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (pw.length < 8) score = Math.min(score, 1);
  return Math.min(score, 4) as StrengthLevel;
}

export function PasswordStrength({ password }: { password: string }) {
  const level = scorePassword(password);
  const filled = password ? level + 1 : 0;

  return (
    <div className="flex flex-col gap-1.5" aria-live="polite">
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.span
            key={i}
            initial={false}
            animate={{ opacity: i < filled ? 1 : 0.15 }}
            transition={{ duration: 0.2 }}
            className={`h-1 flex-1 rounded-full ${
              i < filled ? COLORS[level] : "bg-white/[0.08]"
            }`}
          />
        ))}
      </div>
      <span className="text-[11px] uppercase tracking-[0.18em] text-white/40">
        {password ? LABELS[level] : "Enter a password"}
      </span>
    </div>
  );
}
