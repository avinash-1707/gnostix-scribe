"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { ArrowUpRight, Sparkles } from "lucide-react";

export function CtaSection() {
  return (
    <section className="relative py-24 md:py-32 px-4 md:px-6 bg-[#030303] overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/2 h-[420px] w-[820px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-r from-indigo-500/[0.18] via-violet-500/[0.12] to-rose-500/[0.18] blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.9, ease: [0.25, 0.4, 0.25, 1] as const }}
        className="relative mx-auto max-w-3xl text-center"
      >
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-xs uppercase tracking-[0.2em] text-white/50 mb-8">
          <Sparkles className="h-3 w-3" />
          Free while in preview
        </span>

        <h2 className="text-3xl sm:text-5xl md:text-6xl font-semibold tracking-tight">
          <span className="bg-clip-text text-transparent bg-gradient-to-b from-white to-white/70">
            Ship the tutorial.
          </span>
          <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-white/90 to-rose-300 italic font-light">
            skip the blank page.
          </span>
        </h2>

        <p className="mt-6 text-base md:text-lg text-white/50 font-light leading-relaxed max-w-xl mx-auto">
          One topic, one click. The agent does the research, the writing, and
          the illustrating — you decide what to publish.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/register"
            className="group inline-flex items-center gap-2 bg-white text-[#030303] hover:bg-white/90 px-6 py-3 rounded-md text-sm font-medium transition-colors"
          >
            Create your account
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center text-sm text-white/70 hover:text-white px-6 py-3 rounded-md border border-white/[0.08] hover:border-white/[0.2] transition-colors"
          >
            I already have an account
          </Link>
        </div>
      </motion.div>
    </section>
  );
}
