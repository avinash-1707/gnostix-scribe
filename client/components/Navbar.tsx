"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { getAccessToken, logout, subscribe } from "@/lib/auth";
import {
  getUsage,
  refreshUsage,
  startUsageAuthSync,
  subscribe as subscribeUsage,
} from "@/lib/usage";
import type { Usage } from "@/lib/api";
import { Logo } from "@/components/Logo";

export default function Navbar() {
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean>(false);
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    setAuthed(getAccessToken() !== null);
    setUsage(getUsage());
    const offAuth = subscribe((tok) => setAuthed(tok !== null));
    const offUsage = subscribeUsage((u) => setUsage(u));
    const offSync = startUsageAuthSync();
    if (getAccessToken()) void refreshUsage();
    return () => {
      offAuth();
      offUsage();
      offSync();
    };
  }, []);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <motion.header
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#030303]/70 backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 md:px-6 py-3">
        <Link href="/" className="group flex items-center gap-1">
          <Logo className="h-7 w-7" />
          <span
            style={{ fontFamily: "var(--font-dancing-script)" }}
            className="text-2xl font-semibold leading-none text-white/90 group-hover:text-white transition-colors"
          >
            Scribe
          </span>
        </Link>

        {authed && (
          <div className="flex items-center gap-2">
            {usage && (
              <span
                title={`${usage.used} of ${usage.limit} topics used`}
                className="inline-flex items-center gap-1.5 min-h-9 rounded-md border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-xs text-white/70"
              >
                <Sparkles className="h-3.5 w-3.5 text-white/50" />
                <span className="font-medium text-white/90">
                  {usage.remaining}
                </span>
                <span className="text-white/40">/ {usage.limit} left</span>
              </span>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 min-h-9 rounded-md border border-white/[0.08] hover:border-white/[0.2] px-3 py-1.5 text-sm text-white/70 hover:text-white transition-colors"
            >
              <LogOut className="h-3.5 w-3.5" />
              Logout
            </button>
          </div>
        )}
      </div>
    </motion.header>
  );
}
