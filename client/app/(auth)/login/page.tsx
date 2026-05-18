"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, AlertCircle } from "lucide-react";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.4, 0.25, 1] as const }}
        className="w-full max-w-sm rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm p-8 shadow-[0_8px_40px_-12px_rgba(0,0,0,0.6)]"
      >
        <div className="mb-7">
          <span className="text-xs uppercase tracking-[0.2em] text-white/40">
            Welcome back
          </span>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white/95">
            Log in to{" "}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-white/90 to-rose-300 italic font-light">
              Gnostix
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

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-[0.2em] text-white/40">
              Password
            </span>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md bg-white/[0.03] border border-white/[0.1] px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/[0.3] focus:bg-white/[0.05] transition-colors"
              placeholder="••••••••"
            />
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
            disabled={submitting}
            className="group mt-2 inline-flex items-center justify-center gap-2 min-h-11 rounded-md bg-white px-4 py-2.5 text-sm font-medium text-[#030303] hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Logging in…" : "Log in"}
            {!submitting && (
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            )}
          </button>
        </form>

        <p className="mt-6 text-sm text-white/50">
          No account?{" "}
          <Link
            href="/register"
            className="text-white/90 hover:text-white underline-offset-4 hover:underline transition-colors"
          >
            Create one
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
