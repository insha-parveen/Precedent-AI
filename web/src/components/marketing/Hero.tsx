"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { SplitText } from "./SplitText";
import { BarcodeSlats } from "./BarcodeSlats";

/**
 * Redesigned Hero section matching DeepJudge's signature aesthetic:
 * - Top announcement pill: "Introducing Agent Handoff Protocol"
 * - Editorial Serif centered headline: "Legal AI that starts with everything you know"
 * - Balanced subtext
 * - Generative Barcode Slats visual (document DNA / knowledge waveform)
 * - Primary pill CTA actions
 */
export function Hero() {
  return (
    <section
      data-hero-intro
      className="relative min-h-[90vh] flex flex-col justify-center items-center pt-36 pb-20 overflow-hidden"
    >
      {/* Background radial gradient washes */}
      <div
        data-parallax="0.12"
        className="absolute inset-0 -z-10 pointer-events-none"
        aria-hidden="true"
      >
        <div className="absolute top-[5%] left-1/2 -translate-x-1/2 w-[1100px] h-[550px] rounded-full bg-[radial-gradient(ellipse,rgba(230,225,245,0.7),transparent_70%)] blur-3xl" />
        <div className="absolute top-[20%] right-[10%] w-[450px] h-[450px] rounded-full bg-[radial-gradient(circle,rgba(124,58,237,0.06),transparent_65%)] blur-2xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6 w-full text-center">
        {/* Top Announcement Pill */}
        <div data-reveal className="mb-8 flex justify-center">
          <Link
            href="/app"
            className="group inline-flex items-center gap-2 rounded-full border border-sand-deep bg-paper/80 px-4 py-1.5 text-[12px] font-sans tracking-wide text-ink-60 backdrop-blur-sm transition-all duration-300 hover:border-violet-light hover:text-ink hover:shadow-[0_2px_12px_rgba(124,58,237,0.1)]"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-violet" />
            <span className="font-medium text-ink">Introducing Agent Handoff Protocol</span>
            <ArrowRight className="w-3.5 h-3.5 text-ink-40 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:text-violet" />
          </Link>
        </div>

        {/* Big Editorial Headline */}
        <div className="max-w-4xl mx-auto mb-6">
          <SplitText
            as="h1"
            text="Legal AI that starts with everything you know"
            className="text-[clamp(2.75rem,6.5vw,5.25rem)] font-serif font-normal leading-[1.04] tracking-[-0.03em] text-ink block"
          />
        </div>

        {/* Subtitle */}
        <p
          data-reveal
          className="max-w-3xl mx-auto text-base md:text-lg text-ink-60 leading-relaxed font-sans mb-10"
        >
          Powered by world-class enterprise search, Precedent transforms institutional
          knowledge into structured, governed intelligence that enables legal teams to
          build AI applications, and implement LLM agents and workflows.
        </p>

        {/* CTAs */}
        <div data-reveal className="flex flex-wrap items-center justify-center gap-4 mb-16">
          <Link
            href="/app"
            data-magnetic
            className="group inline-flex items-center gap-2 rounded-full bg-ink px-7 py-3.5 text-sm font-medium text-canvas transition-all duration-300 hover:bg-ink-light hover:gap-3.5 shadow-sm"
          >
            Ask the agent
            <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#platform"
            className="inline-flex items-center gap-2 rounded-full border border-sand-deep bg-paper/60 px-7 py-3.5 text-sm font-medium text-ink transition-colors duration-300 hover:bg-sand/60"
          >
            Book Demo
          </a>
        </div>

        {/* Signature Barcode Slats Visual */}
        <div
          data-reveal
          className="w-full max-w-5xl mx-auto border-t border-b border-sand/80 py-4 my-4"
        >
          <BarcodeSlats />
        </div>
      </div>

      {/* Scroll cue */}
      <div
        data-scroll-cue
        className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        aria-hidden="true"
      >
        <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-ink-40">
          Scroll
        </span>
        <span data-cue-line className="w-px h-8 bg-sand-deep" />
      </div>
    </section>
  );
}
