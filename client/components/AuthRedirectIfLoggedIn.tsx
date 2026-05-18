"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { bootstrapAuth } from "@/lib/auth";

export function AuthRedirectIfLoggedIn({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [state, setState] = useState<"checking" | "anonymous">("checking");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await bootstrapAuth();
      if (cancelled) return;
      if (token) {
        router.replace("/dashboard");
      } else {
        setState("anonymous");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (state === "checking") {
    return (
      <div className="flex min-h-[calc(100vh-65px)] items-center justify-center text-sm text-white/50">
        <Loader2 className="h-4 w-4 animate-spin text-white/40 mr-2" />
        Checking session…
      </div>
    );
  }

  return <>{children}</>;
}
