"use client";

import { motion } from "motion/react";

interface SectionHeadingProps {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: "left" | "center";
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
}: SectionHeadingProps) {
  const alignClass = align === "center" ? "items-center text-center" : "items-start text-left";

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.8, ease: [0.25, 0.4, 0.25, 1] as const }}
      className={`flex flex-col ${alignClass} max-w-2xl ${align === "center" ? "mx-auto" : ""}`}
    >
      {eyebrow && (
        <span className="text-xs uppercase tracking-[0.2em] text-white/40 mb-4">
          {eyebrow}
        </span>
      )}
      <h2 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-white/95">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base md:text-lg text-white/50 font-light leading-relaxed max-w-xl">
          {description}
        </p>
      )}
    </motion.div>
  );
}
