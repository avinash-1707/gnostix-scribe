import { LandingNav } from "@/components/landing/LandingNav";
import { HeroSection } from "@/components/landing/HeroSection";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { StackSection } from "@/components/landing/StackSection";
import { CtaSection } from "@/components/landing/CtaSection";
import { FooterSection } from "@/components/landing/FooterSection";
import { LenisProvider } from "@/components/landing/LenisProvider";

export default function Home() {
  return (
    <LenisProvider>
      <div className="relative min-h-screen bg-[#030303] text-white antialiased selection:bg-white/15 selection:text-white">
        <LandingNav />
        <main>
          <HeroSection />
          <FeaturesSection />
          <HowItWorksSection />
          <StackSection />
          <CtaSection />
        </main>
        <FooterSection />
      </div>
    </LenisProvider>
  );
}
