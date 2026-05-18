"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { Feather } from "lucide-react";

export function LandingNav() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-[#030303]/60 border-b border-white/[0.06]"
    >
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 md:px-6 py-4">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="grid place-items-center h-8 w-8 rounded-md bg-gradient-to-br from-indigo-400/30 to-rose-400/30 border border-white/[0.08] group-hover:border-white/[0.18] transition-colors">
            <Feather className="h-4 w-4 text-white/80" />
          </span>
          <span className="text-sm font-medium tracking-wide text-white/90">
            Gnostix Scribe
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8 text-sm text-white/50">
          <a
            href="#features"
            className="hover:text-white/90 transition-colors"
          >
            Features
          </a>
          <a
            href="#how-it-works"
            className="hover:text-white/90 transition-colors"
          >
            How it works
          </a>
          <a href="#stack" className="hover:text-white/90 transition-colors">
            Stack
          </a>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="hidden sm:inline-flex items-center text-sm text-white/60 hover:text-white/90 px-3 py-2 transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center text-sm text-[#030303] bg-white hover:bg-white/90 px-3.5 py-2 rounded-md font-medium transition-colors"
          >
            Get started
          </Link>
        </div>
      </nav>
    </motion.header>
  );
}
