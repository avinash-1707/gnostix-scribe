"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, AlertCircle, ArrowLeft, Check } from "lucide-react";
import { login, register } from "@/lib/auth";
import { PasswordInput } from "@/components/auth/PasswordInput";
import {
  PasswordStrength,
  scorePassword,
} from "@/components/auth/PasswordStrength";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const mismatch = confirm.length > 0 && confirm !== password;
  const strength = scorePassword(password);
  const canSubmit =
    email &&
    password.length >= 8 &&
    confirm === password &&
    accepted &&
    strength >= 2;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mismatch) {
      setError("Passwords do not match");
      return;
    }
    if (!accepted) {
      setError("Accept the terms to continue");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password);
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-120px)] items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm flex flex-col gap-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 self-start text-xs uppercase tracking-[0.2em] text-white/40 hover:text-white/80 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to landing
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.25, 0.4, 0.25, 1] as const }}
          className="rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm p-8 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.6)]"
        >
          <div className="mb-7">
            <span className="text-xs uppercase tracking-[0.2em] text-white/40">
              Get started
            </span>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white/95">
              Create an{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-white/90 to-rose-300 italic font-light">
                account
              </span>
            </h1>
          </div>

          <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-[0.2em] text-white/40">
                Email
              </span>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md bg-white/[0.03] border border-white/[0.1] px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/[0.3] focus:bg-white/[0.05] transition-colors"
                placeholder="you@example.com"
              />
            </label>

            <div className="flex flex-col gap-2">
              <PasswordInput
                label="Password"
                value={password}
                onChange={setPassword}
                autoComplete="new-password"
                minLength={8}
                placeholder="At least 8 characters"
              />
              <PasswordStrength password={password} />
            </div>

            <div className="flex flex-col gap-2">
              <PasswordInput
                label="Confirm Password"
                value={confirm}
                onChange={setConfirm}
                autoComplete="new-password"
                minLength={8}
                placeholder="Re-enter your password"
              />
              {mismatch && (
                <span className="text-xs text-rose-300/90">
                  Passwords do not match
                </span>
              )}
              {!mismatch && confirm.length > 0 && confirm === password && (
                <span className="inline-flex items-center gap-1 text-xs text-emerald-300/90">
                  <Check className="h-3 w-3" />
                  Passwords match
                </span>
              )}
            </div>

            <label className="flex items-start gap-2.5 cursor-pointer select-none">
              <span className="relative mt-0.5 inline-grid place-items-center">
                <input
                  type="checkbox"
                  checked={accepted}
                  onChange={(e) => setAccepted(e.target.checked)}
                  className="peer h-4 w-4 appearance-none rounded border border-white/[0.2] bg-white/[0.03] checked:bg-white checked:border-white focus:outline-none focus:ring-1 focus:ring-white/30 transition-colors"
                />
                <Check className="pointer-events-none absolute h-3 w-3 text-[#030303] opacity-0 peer-checked:opacity-100" />
              </span>
              <span className="text-xs leading-relaxed text-white/60">
                I agree to the{" "}
                <Link
                  href="/terms"
                  className="text-white/85 underline-offset-4 hover:underline"
                >
                  Terms
                </Link>{" "}
                and{" "}
                <Link
                  href="/privacy"
                  className="text-white/85 underline-offset-4 hover:underline"
                >
                  Privacy Policy
                </Link>
                .
              </span>
            </label>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 rounded-md border border-rose-500/[0.2] bg-rose-500/[0.06] px-3 py-2 text-sm text-rose-300"
                role="alert"
              >
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                {error}
              </motion.p>
            )}

            <button
              type="submit"
              disabled={submitting || !canSubmit}
              className="group mt-2 inline-flex items-center justify-center gap-2 min-h-11 rounded-md bg-white px-4 py-2.5 text-sm font-medium text-[#030303] hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? "Creating account…" : "Create account"}
              {!submitting && (
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              )}
            </button>
          </form>

          <p className="mt-6 text-sm text-white/50">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-white/90 hover:text-white underline-offset-4 hover:underline transition-colors"
            >
              Log in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
