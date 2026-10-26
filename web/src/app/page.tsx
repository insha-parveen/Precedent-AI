"use client";

import { ClosingCta } from "@/components/marketing/ClosingCta";
import { Footer } from "@/components/marketing/Footer";
import { Hero } from "@/components/marketing/Hero";
import { InsightsBlog } from "@/components/marketing/InsightsBlog";
import { KnowledgeConstellation } from "@/components/marketing/KnowledgeConstellation";
import { Nav } from "@/components/marketing/Nav";
import { PlatformArchitecture } from "@/components/marketing/PlatformArchitecture";
import { SearchShowcase } from "@/components/marketing/SearchShowcase";
import { Stats } from "@/components/marketing/Stats";
import { TestimonialsDark } from "@/components/marketing/TestimonialsDark";
import { WorkflowShowcase } from "@/components/marketing/WorkflowShowcase";
import { useMarketingAnimations } from "@/lib/animations";

/**
 * Marketing landing page redesigned to match DeepJudge's visual layout,
 * color palette, typography hierarchy, and Webflow/GSAP motion craft:
 *
 * 1. Nav with brand mark and floating pill
 * 2. Hero: Announcement, Editorial Serif, Barcode Slats wave visual
 * 3. Search Showcase: "The only AI platform that knows..." + Slats matrix + interactive search
 * 4. Knowledge Constellation: "Your collective knowledge is your unique asset" + interactive graph
 * 5. Workflow Builder: "Automate mission-critical workflows with ease" + modular UI cards
 * 6. Platform Architecture: "The one platform for your AI strategy" + role switcher & stacked tiers
 * 7. Quantified Impact: +65%, +85%, +23, +4x ROI, 90% metrics + client logo ticker
 * 8. Dark Editorial Testimonials: High-contrast charcoal section
 * 9. Insights / Blog: 3 pastel editorial cards
 * 10. Closing CTA & Comprehensive Footer
 */
export default function Home() {
  useMarketingAnimations();

  return (
    <>
      <div data-progress className="scroll-progress" aria-hidden="true" />
      <Nav />
      <main>
        <Hero />
        <SearchShowcase />
        <KnowledgeConstellation />
        <WorkflowShowcase />
        <PlatformArchitecture />
        <Stats />
        <TestimonialsDark />
        <InsightsBlog />
        <ClosingCta />
      </main>
      <Footer />
    </>
  );
}
