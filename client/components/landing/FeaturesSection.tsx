"use client";

import { motion } from "motion/react";
import {
  Radio,
  Workflow,
  ImageIcon,
  ShieldCheck,
  History,
  FileCode2,
} from "lucide-react";
import { SectionHeading } from "./SectionHeading";

const features = [
  {
    icon: Workflow,
    title: "10-node LangGraph agent",
    body: "Parallel scrape fan-out, coverage loops, conditional image generation, validator retries — all wired as a graph, not a script.",
  },
  {
    icon: Radio,
    title: "Live SSE timeline",
    body: "Every node transition streams to your dashboard in real time. See exactly what the agent is doing, when, and why.",
  },
  {
    icon: ImageIcon,
    title: "Auto-illustrated",
    body: "Content analyser decides where visuals belong, Imagen + GPT-Image generate them, Cloudinary hosts them. You just copy the MDX.",
  },
  {
    icon: ShieldCheck,
    title: "Validator on guard",
    body: "Every output passes a strict MDX schema check — frontmatter, callouts, figures, code fences — or loops back for another pass.",
  },
  {
    icon: FileCode2,
    title: "Publication-ready MDX",
    body: "Output adheres to a fixed component schema. Drop it into any MDX-aware site — no manual edits, no rewriting.",
  },
  {
    icon: History,
    title: "History, kept",
    body: "Every generation lands in Postgres against your account. Revisit, recopy, or rerun without re-paying the agent tax.",
  },
];

export function FeaturesSection() {
  return (
    <section
      id="features"
      className="relative py-24 md:py-32 px-4 md:px-6 bg-[#030303]"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          eyebrow="What it does"
          title="A research desk, a writer, and an illustrator — wired together."
          description="Six capabilities you don't have to glue yourself."
        />

        <div className="mt-16 grid gap-px sm:grid-cols-2 lg:grid-cols-3 bg-white/[0.06] border border-white/[0.06] rounded-xl overflow-hidden">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{
                  duration: 0.7,
                  delay: i * 0.08,
                  ease: [0.25, 0.4, 0.25, 1] as const,
                }}
                className="group relative bg-[#030303] p-8 hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/[0.04] border border-white/[0.08] mb-5 group-hover:border-white/[0.18] transition-colors">
                  <Icon className="h-5 w-5 text-white/80" />
                </div>
                <h3 className="text-lg font-medium text-white/90 mb-2 tracking-tight">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-white/50">
                  {f.body}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
