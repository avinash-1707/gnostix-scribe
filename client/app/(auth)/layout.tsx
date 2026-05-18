import Link from "next/link";
import { Logo } from "@/components/Logo";
import { AuthRedirectIfLoggedIn } from "@/components/AuthRedirectIfLoggedIn";

export default function AuthLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#030303] text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[420px] w-[820px] rounded-full bg-gradient-to-r from-indigo-500/[0.12] via-violet-500/[0.08] to-rose-500/[0.12] blur-3xl" />
      </div>
      <header className="relative z-10 flex justify-center px-4 pt-8">
        <Link
          href="/"
          aria-label="Gnostix Scribe — back to landing page"
          className="group inline-flex items-center gap-1"
        >
          <Logo className="h-8 w-8" />
          <span
            style={{ fontFamily: "var(--font-dancing-script)" }}
            className="text-2xl font-semibold leading-none text-white/90 group-hover:text-white transition-colors"
          >
            Scribe
          </span>
        </Link>
      </header>
      <main className="relative flex-1">
        <AuthRedirectIfLoggedIn>{children}</AuthRedirectIfLoggedIn>
      </main>
    </div>
  );
}
