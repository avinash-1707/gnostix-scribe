"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Check, Copy } from "lucide-react";

interface CopyableMdxProps {
  mdx: string;
}

export function CopyableMdx({ mdx }: CopyableMdxProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(mdx);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="relative rounded-xl border border-white/[0.08] bg-[#0a0a0a]">
      <button
        type="button"
        onClick={handleCopy}
        className="absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.06] px-2.5 py-1 text-[11px] font-medium text-white/80 hover:bg-white/[0.1] hover:text-white transition-colors backdrop-blur-sm"
        aria-label="copy mdx"
      >
        {copied ? (
          <>
            <Check className="h-3 w-3 text-emerald-400" />
            Copied
          </>
        ) : (
          <>
            <Copy className="h-3 w-3" />
            Copy
          </>
        )}
      </button>
      <pre className="max-h-96 overflow-auto px-5 py-4 pr-24 font-mono text-sm text-white/85 leading-relaxed whitespace-pre-wrap break-words">
        {mdx}
      </pre>
    </div>
  );
}

interface MdxOutputBoxProps {
  topic: string;
  mdx: string;
}

export default function MdxOutputBox({ topic, mdx }: MdxOutputBoxProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="flex flex-col gap-3"
    >
      <h3 className="text-base font-medium text-white/90 break-words tracking-tight">
        {topic}
      </h3>
      <CopyableMdx mdx={mdx} />
    </motion.section>
  );
}
