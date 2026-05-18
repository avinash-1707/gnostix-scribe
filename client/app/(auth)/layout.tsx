import Navbar from "@/components/Navbar";
import { AuthRedirectIfLoggedIn } from "@/components/AuthRedirectIfLoggedIn";

export default function AuthLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#030303] text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[420px] w-[820px] rounded-full bg-gradient-to-r from-indigo-500/[0.12] via-violet-500/[0.08] to-rose-500/[0.12] blur-3xl" />
      </div>
      <Navbar />
      <main className="relative flex-1">
        <AuthRedirectIfLoggedIn>{children}</AuthRedirectIfLoggedIn>
      </main>
    </div>
  );
}
