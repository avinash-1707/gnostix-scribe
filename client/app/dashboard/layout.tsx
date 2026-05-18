import Navbar from "@/components/Navbar";

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#030303] text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 right-[-10%] h-[420px] w-[620px] rounded-full bg-gradient-to-br from-indigo-500/[0.08] to-transparent blur-3xl" />
        <div className="absolute top-[40%] left-[-10%] h-[380px] w-[520px] rounded-full bg-gradient-to-br from-rose-500/[0.06] to-transparent blur-3xl" />
      </div>
      <Navbar />
      <main className="relative flex-1">{children}</main>
    </div>
  );
}
