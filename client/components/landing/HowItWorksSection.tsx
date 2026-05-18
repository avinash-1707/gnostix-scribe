"use client";

import { motion } from "motion/react";
import {
  GitBranch,
  Globe2,
  BookOpen,
  Brain,
  Merge,
  ScanSearch,
  ImagePlus,
  PenLine,
  ShieldCheck,
  FileDown,
  type LucideIcon,
} from "lucide-react";
import { SectionHeading } from "./SectionHeading";

interface Node {
  id: string;
  label: string;
  hint: string;
  icon: LucideIcon;
  group: "route" | "research" | "synthesize" | "render";
}

const nodes: Node[] = [
  {
    id: "topic_router",
    label: "Routing Topic",
    hint: "Validates input, builds source URLs, seeds graph state.",
    icon: GitBranch,
    group: "route",
  },
  {
    id: "gfg_scraper",
    label: "Scraping GeeksForGeeks",
    hint: "Trafilatura pulls clean prose from GFG.",
    icon: Globe2,
    group: "research",
  },
  {
    id: "tpointtech_scraper",
    label: "Scraping TpointTech",
    hint: "Parallel scrape — second source for cross-check.",
    icon: BookOpen,
    group: "research",
  },
  {
    id: "llm_knowledge",
    label: "Generating LLM Knowledge",
    hint: "Gemini fills in what the scrapers missed.",
    icon: Brain,
    group: "research",
  },
  {
    id: "content_merger",
    label: "Merging Content",
    hint: "Coverage check loops until ≥ 400 words, 2 sections, 1 code block.",
    icon: Merge,
    group: "synthesize",
  },
  {
    id: "content_analyser",
    label: "Analysing Content",
    hint: "Decides which concepts need a diagram or illustration.",
    icon: ScanSearch,
    group: "synthesize",
  },
  {
    id: "image_generator",
    label: "Generating Images",
    hint: "Imagen → Cloudinary. Falls back to gpt-image-1 on failure.",
    icon: ImagePlus,
    group: "synthesize",
  },
  {
    id: "mdx_generator",
    label: "Generating MDX",
    hint: "Strict schema: frontmatter, callouts, figures, code fences.",
    icon: PenLine,
    group: "render",
  },
  {
    id: "mdx_validator",
    label: "Validating MDX",
    hint: "Hard checks; retries the generator up to 3× on a miss.",
    icon: ShieldCheck,
    group: "render",
  },
  {
    id: "file_writer",
    label: "Writing Output File",
    hint: "Stages the .mdx, commits to Postgres, hands it to you.",
    icon: FileDown,
    group: "render",
  },
];

const groupAccent: Record<Node["group"], string> = {
  route: "from-cyan-400/60 to-cyan-400/0",
  research: "from-indigo-400/60 to-indigo-400/0",
  synthesize: "from-violet-400/60 to-violet-400/0",
  render: "from-rose-400/60 to-rose-400/0",
};

export function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="relative py-24 md:py-32 px-4 md:px-6 bg-[#030303] overflow-hidden"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.08),transparent_55%)]" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      <div className="relative mx-auto max-w-5xl">
        <SectionHeading
          eyebrow="The pipeline"
          title="Ten nodes. One topic in, one MDX file out."
          description="Each step streams to your dashboard. Retries are visible. Failures are explained, not swallowed."
        />

        <div className="relative mt-16">
          <div
            aria-hidden
            className="absolute left-6 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-white/[0.12] to-transparent md:-translate-x-px"
          />

          <ol className="space-y-6 md:space-y-10">
            {nodes.map((node, i) => {
              const Icon = node.icon;
              const onRight = i % 2 === 1;
              return (
                <motion.li
                  key={node.id}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-80px" }}
                  transition={{
                    duration: 0.7,
                    delay: i * 0.05,
                    ease: [0.25, 0.4, 0.25, 1] as const,
                  }}
                  className={`relative pl-16 md:pl-0 md:grid md:grid-cols-2 md:gap-12 md:items-center ${
                    onRight ? "md:[&>div:first-child]:order-2" : ""
                  }`}
                >
                  <div
                    className={`relative ${
                      onRight ? "md:text-left md:pl-12" : "md:text-right md:pr-12"
                    }`}
                  >
                    <div className="inline-flex md:inline-block items-baseline gap-3">
                      <span className="text-xs font-mono text-white/30 tracking-wider">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <h3 className="text-lg md:text-xl font-medium text-white/90 tracking-tight">
                        {node.label}
                      </h3>
                    </div>
                    <p className="mt-1.5 text-sm text-white/45 leading-relaxed max-w-sm md:inline-block">
                      {node.hint}
                    </p>
                  </div>

                  <div
                    aria-hidden
                    className="absolute left-0 md:left-1/2 top-1 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2"
                  >
                    <span
                      className={`absolute inset-0 -m-3 rounded-full bg-gradient-to-br ${groupAccent[node.group]} blur-xl opacity-70`}
                    />
                    <span className="relative grid h-12 w-12 place-items-center rounded-full bg-[#0a0a0a] border border-white/[0.1] shadow-[0_0_0_4px_rgba(3,3,3,1)]">
                      <Icon className="h-5 w-5 text-white/80" />
                    </span>
                  </div>

                  <div className="hidden md:block" />
                </motion.li>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}
