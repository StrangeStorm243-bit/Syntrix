import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { DemoEmbed } from "@/components/DemoEmbed";
import { TrustBar } from "@/components/TrustBar";
import { Pipeline } from "@/components/Pipeline";
import { GetStartedCTA } from "@/components/GetStartedCTA";
import { Features } from "@/components/Features";
import { TerminalShowcase } from "@/components/TerminalShowcase";
import { QuickStart } from "@/components/QuickStart";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="bg-base">
        <Hero />
        <DemoEmbed />
        <TrustBar />
        <Pipeline />
        <GetStartedCTA />
        <Features />
        <TerminalShowcase />
        <QuickStart />
      </main>
      <Footer />
    </>
  );
}
