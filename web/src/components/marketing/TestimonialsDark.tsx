"use client";

import { SplitText } from "./SplitText";
import { Quote } from "lucide-react";

/**
 * Section 8 from DeepJudge:
 * High-contrast dark charcoal section (#141412) with editorial serif typography
 * and customer testimonial quote cards.
 */
const TESTIMONIALS = [
  {
    org: "HOMBURGER",
    quote:
      "The adoption rate has been remarkable, with more than 80% of our lawyers actively querying prior agreements, with a level of engagement that is unparalleled compared with other legal tech tools.",
    author: "David Oser",
    role: "Partner at Homburger",
    avatar: "DO",
  },
  {
    org: "INNOVATION COUNSEL",
    quote:
      "Instead of hunting for documents to upload to an AI platform, everything you need is already there. Fast, efficient, and compliant access to the right information is the foundation for all applications that help us do more with our knowledge base.",
    author: "Joe Green",
    role: "Chief Innovation Officer",
    avatar: "JG",
  },
  {
    org: "FRESHFIELDS",
    quote:
      "Innovation is about strengthening how we work and preparing for what's next. Precedent supports that by enabling responsible, targeted use of proprietary knowledge and powering bespoke AI workflows tailored to our standards.",
    author: "Ed Pease",
    role: "Global Innovation Lead",
    avatar: "EP",
  },
];

export function TestimonialsDark() {
  return (
    <section className="py-28 md:py-40 bg-[#141412] text-canvas relative overflow-hidden">
      {/* Subtle radial backdrop glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[radial-gradient(circle,rgba(124,58,237,0.08),transparent_70%)] blur-3xl pointer-events-none"
        aria-hidden="true"
      />

      <div className="max-w-4xl mx-auto px-6 text-center">
        {/* Editorial Heading */}
        <div className="mb-20">
          <SplitText
            as="h2"
            text="What people say about Precedent"
            className="text-[clamp(2.5rem,5vw,4.25rem)] font-serif font-normal leading-[1.06] tracking-[-0.03em] text-canvas block"
          />
        </div>

        {/* Stacked Testimonial Cards matching DeepJudge visual layout */}
        <div data-reveal-group className="flex flex-col gap-6 text-left">
          {TESTIMONIALS.map((item, idx) => (
            <div
              key={idx}
              data-reveal-item
              className="bg-[#1c1c1a] border border-[#2c2c28] rounded-3xl p-8 sm:p-10 shadow-lg hover:border-[#3e3e38] transition-colors duration-300"
            >
              {/* Firm Tag */}
              <div className="flex items-center justify-between mb-6">
                <span className="text-[11px] font-mono tracking-widest uppercase text-canvas/50">
                  {item.org}
                </span>
                <Quote className="w-5 h-5 text-canvas/20" />
              </div>

              {/* Quote Body */}
              <p className="font-serif text-base sm:text-lg text-canvas/90 leading-relaxed mb-8">
                &ldquo;{item.quote}&rdquo;
              </p>

              {/* Author Info */}
              <div className="flex items-center gap-3.5 pt-6 border-t border-[#2c2c28]">
                <div className="w-10 h-10 rounded-full bg-violet/20 border border-violet/40 text-violet-light font-mono text-xs font-semibold flex items-center justify-center">
                  {item.avatar}
                </div>
                <div>
                  <h4 className="text-sm font-medium text-canvas">{item.author}</h4>
                  <p className="text-xs text-canvas/50 font-sans">{item.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
