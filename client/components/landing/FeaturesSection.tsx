"use client";

import { motion } from "motion/react";
import {
  Radio,
  Workflow,
  ImageIcon,
  ShieldCheck,
  History,
  FileCode2,
  type LucideIcon,
} from "lucide-react";
import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { SectionHeading } from "./SectionHeading";

const features = [
  {
    icon: Workflow,
    title: "10-node LangGraph agent",
    body: "Parallel scrape fan-out, coverage loops, conditional image generation, validator retries — all wired as a graph, not a script.",
    span: "lg:col-span-2",
  },
  {
    icon: Radio,
    title: "Live SSE timeline",
    body: "Every node transition streams to your dashboard in real time. See exactly what the agent is doing, when, and why.",
    span: "lg:col-span-1",
  },
  {
    icon: ImageIcon,
    title: "Auto-illustrated",
    body: "Content analyser decides where visuals belong, Imagen + GPT-Image generate them, Cloudinary hosts them. You just copy the MDX.",
    span: "lg:col-span-1",
  },
  {
    icon: ShieldCheck,
    title: "Validator on guard",
    body: "Every output passes a strict MDX schema check — frontmatter, callouts, figures, code fences — or loops back for another pass.",
    span: "lg:col-span-2",
  },
  {
    icon: FileCode2,
    title: "Publication-ready MDX",
    body: "Output adheres to a fixed component schema. Drop it into any MDX-aware site — no manual edits, no rewriting.",
    span: "lg:col-span-2",
  },
  {
    icon: History,
    title: "History, kept",
    body: "Every generation lands in Postgres against your account. Revisit, recopy, or rerun without re-paying the agent tax.",
    span: "lg:col-span-1",
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

        <div className="mx-auto mt-16 grid gap-4 lg:grid-cols-3">
          {features.map((f, i) => (
            <FeatureCard key={f.title} index={i} className={f.span}>
              <CardHeading
                icon={f.icon}
                title={f.title}
                description={f.body}
              />
            </FeatureCard>
          ))}
        </div>
      </div>
    </section>
  );
}

interface FeatureCardProps {
  children: ReactNode;
  className?: string;
  index: number;
}

function FeatureCard({ children, className, index }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{
        duration: 0.7,
        delay: index * 0.08,
        ease: [0.25, 0.4, 0.25, 1] as const,
      }}
      className={cn(
        "group relative border border-white/[0.08] bg-white/[0.015] hover:bg-white/[0.035] transition-colors",
        className
      )}
    >
      <CardDecorator />
      <div className="pointer-events-none absolute inset-0 [background:radial-gradient(120%_120%_at_50%_0%,transparent_55%,rgba(255,255,255,0.04)_100%)]" />
      <div className="relative">{children}</div>
    </motion.div>
  );
}

function CardDecorator() {
  return (
    <>
      <span className="absolute -left-px -top-px block size-2 border-l-2 border-t-2 border-white/50" />
      <span className="absolute -right-px -top-px block size-2 border-r-2 border-t-2 border-white/50" />
      <span className="absolute -bottom-px -left-px block size-2 border-b-2 border-l-2 border-white/50" />
      <span className="absolute -bottom-px -right-px block size-2 border-b-2 border-r-2 border-white/50" />
    </>
  );
}

interface CardHeadingProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

function CardHeading({ icon: Icon, title, description }: CardHeadingProps) {
  return (
    <div className="p-6 md:p-8">
      <span className="flex items-center gap-2 text-sm text-white/80">
        <Icon className="size-4" />
        {title}
      </span>
      <p className="mt-8 text-xl md:text-2xl font-semibold leading-snug tracking-tight text-white">
        {description}
      </p>
    </div>
  );
}
