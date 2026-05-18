"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Feather, LogOut } from "lucide-react";
import { motion } from "motion/react";
import { getAccessToken, logout, subscribe } from "@/lib/auth";

export default function Navbar() {
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean>(false);

  useEffect(() => {
    setAuthed(getAccessToken() !== null);
    return subscribe((tok) => setAuthed(tok !== null));
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
        <Link
          href={authed ? "/dashboard" : "/"}
          className="group flex items-center gap-2"
        >
          <span className="grid place-items-center h-8 w-8 rounded-md bg-gradient-to-br from-indigo-400/30 to-rose-400/30 border border-white/[0.08] group-hover:border-white/[0.18] transition-colors">
            <Feather className="h-4 w-4 text-white/80" />
          </span>
          <span className="text-sm font-medium tracking-wide text-white/90">
            Gnostix Scribe
          </span>
        </Link>

        {authed && (
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center gap-2 min-h-9 rounded-md border border-white/[0.08] hover:border-white/[0.2] px-3 py-1.5 text-sm text-white/70 hover:text-white transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            Logout
          </button>
        )}
      </div>
    </motion.header>
  );
}
