"use client";

import { useState } from "react";

interface TopicFormProps {
  disabled?: boolean;
  onSubmit: (topicsRaw: string) => void;
}

export default function TopicForm({ disabled, onSubmit }: TopicFormProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-4 md:p-6">
      <h2 className="text-lg font-semibold text-gray-900">New generation</h2>
      <form className="mt-4 flex flex-col gap-3" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium text-gray-700">Topics</span>
          <textarea
            rows={4}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Enter topics, one per line or comma-separated"
            disabled={disabled}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </label>
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="self-end min-h-11 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {disabled ? "Running…" : "Generate"}
        </button>
      </form>
    </section>
  );
}
