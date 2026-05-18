"use client";

import { useState } from "react";

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
    <div className="relative rounded-lg border border-gray-200 bg-gray-900">
      <button
        type="button"
        onClick={handleCopy}
        className="absolute right-2 top-2 min-h-9 rounded-md bg-gray-700 px-3 py-1 text-xs font-medium text-gray-100 hover:bg-gray-600"
      >
        {copied ? "Copied" : "Copy"}
      </button>
      <pre className="max-h-96 overflow-auto px-4 py-3 pr-20 font-mono text-sm text-gray-100 whitespace-pre-wrap break-words">
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
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold text-gray-900 break-words">{topic}</h2>
      <CopyableMdx mdx={mdx} />
    </section>
  );
}
