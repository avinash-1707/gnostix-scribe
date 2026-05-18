"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { HeroGeometric } from "@/components/ui/shape-landing-hero";

export function HeroSection() {
  return (
    <HeroGeometric
      badge="Tutorials, on demand"
      title1="Type a topic."
      title2="Get a tutorial."
      description="Tell Gnostix Scribe what you want to learn. Minutes later you get a clear, hands-on guide, written from real sources, with the diagrams and code already in place. Read it, share it, or drop it straight into your blog."
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
          See how it works
        </a>
      </div>
    </HeroGeometric>
  );
}
