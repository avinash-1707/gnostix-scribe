"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getAccessToken, logout, subscribe } from "@/lib/auth";

export default function Navbar() {
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean>(false);

  useEffect(() => {
    setAuthed(getAccessToken() !== null);
    return subscribe((tok) => setAuthed(tok !== null));
  }, []);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <Link
          href="/dashboard"
          className="text-xl font-semibold text-gray-900"
        >
          Gnostix Scribe
        </Link>
        {authed && (
          <button
            type="button"
            onClick={handleLogout}
            className="min-h-11 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
}
