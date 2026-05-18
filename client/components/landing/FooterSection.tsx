"use client";

import Link from "next/link";
import { Feather } from "lucide-react";

export function FooterSection() {
  return (
    <footer className="relative border-t border-white/[0.06] bg-[#030303] px-4 md:px-6 py-12">
      <div className="mx-auto max-w-6xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <span className="grid place-items-center h-7 w-7 rounded-md bg-gradient-to-br from-indigo-400/30 to-rose-400/30 border border-white/[0.08]">
            <Feather className="h-3.5 w-3.5 text-white/80" />
          </span>
          <span className="text-sm text-white/70">Gnostix Scribe</span>
          <span className="text-xs text-white/30 ml-2">
            © {new Date().getFullYear()}
          </span>
        </div>

        <nav className="flex items-center gap-6 text-sm text-white/40">
          <a href="#features" className="hover:text-white/80 transition-colors">
            Features
          </a>
          <a
            href="#how-it-works"
            className="hover:text-white/80 transition-colors"
          >
            Pipeline
          </a>
          <Link
            href="/login"
            className="hover:text-white/80 transition-colors"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="hover:text-white/80 transition-colors"
          >
            Sign up
          </Link>
        </nav>
      </div>
    </footer>
  );
}
