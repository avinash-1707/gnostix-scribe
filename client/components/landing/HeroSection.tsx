"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { HeroGeometric } from "@/components/ui/shape-landing-hero";

export function HeroSection() {
  return (
    <HeroGeometric
      badge="LangGraph · MDX · Live SSE"
      title1="Type a topic."
      title2="ship a tutorial."
      description="Gnostix Scribe pipes any technical topic through a 10-node LangGraph agent — scraping, reasoning, illustrating, validating — and hands back a publication-ready MDX file you can paste anywhere."
    >
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-4">
        <Link
          href="/register"
          className="group inline-flex items-center gap-2 bg-white text-[#030303] hover:bg-white/90 px-5 py-3 rounded-md text-sm font-medium transition-colors"
        >
          Start generating
          <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </Link>
        <a
          href="#how-it-works"
          className="inline-flex items-center gap-2 text-white/70 hover:text-white px-5 py-3 rounded-md text-sm border border-white/[0.08] hover:border-white/[0.2] transition-colors"
        >
          See the pipeline
        </a>
      </div>
    </HeroGeometric>
  );
}
