"use client";

import { motion } from "motion/react";

const stack = [
  { label: "LangGraph", desc: "Agent graph" },
  { label: "FastAPI", desc: "SSE backend" },
  { label: "Gemini 2.5", desc: "Reasoning" },
  { label: "Imagen + GPT-Image", desc: "Visuals" },
  { label: "Cloudinary", desc: "Image CDN" },
  { label: "Postgres", desc: "History store" },
  { label: "Next.js 16", desc: "Client" },
];

export function StackSection() {
  return (
    <section
      id="stack"
      className="relative py-20 md:py-24 px-4 md:px-6 bg-[#030303] border-y border-white/[0.06]"
    >
      <div className="mx-auto max-w-6xl">
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.7, ease: [0.25, 0.4, 0.25, 1] as const }}
          className="text-xs uppercase tracking-[0.2em] text-white/40 text-center mb-10"
        >
          Powered by
        </motion.p>

        <ul className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-px bg-white/[0.06] rounded-lg overflow-hidden border border-white/[0.06]">
          {stack.map((s, i) => (
            <motion.li
              key={s.label}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.05 }}
              className="bg-[#030303] px-4 py-5 text-center hover:bg-white/[0.03] transition-colors"
            >
              <div className="text-sm font-medium text-white/85 tracking-tight">
                {s.label}
              </div>
              <div className="mt-1 text-[11px] text-white/35 uppercase tracking-wider">
                {s.desc}
              </div>
            </motion.li>
          ))}
        </ul>
      </div>
    </section>
  );
}
