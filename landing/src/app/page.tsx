import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { TrustBar } from "@/components/TrustBar";
import { Pipeline } from "@/components/Pipeline";
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
        <TrustBar />
        <Pipeline />
        <Features />
        <TerminalShowcase />
        <QuickStart />
      </main>
      <Footer />
    </>
  );
}
