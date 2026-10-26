"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { SplitText } from "./SplitText";

export function ClosingCta() {
  return (
    <section className="py-28 md:py-40">
      <div className="max-w-7xl mx-auto px-6">
        <div
          data-cta-pulse
          className="relative overflow-hidden rounded-3xl bg-ink text-canvas px-8 py-20 md:px-20 md:py-28 text-center"
        >
          <div
            data-parallax="0.1"
            className="absolute inset-0 pointer-events-none"
            aria-hidden="true"
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] rounded-full bg-[radial-gradient(ellipse,rgba(242,240,237,0.09),transparent_65%)] blur-3xl" />
          </div>

          <div className="relative">
            <p
              data-reveal
              className="text-[11px] font-mono uppercase tracking-[0.2em] text-canvas/40 mb-6"
            >
              Get started
            </p>
            <SplitText
              as="h2"
              text="Ask it something your chat model cannot answer."
              className="text-[clamp(2rem,5vw,3.75rem)] font-medium leading-[1.05] tracking-[-0.025em] block max-w-3xl mx-auto mb-8"
            />
            <p
              data-reveal
              className="max-w-xl mx-auto text-lg text-canvas/60 leading-relaxed mb-10"
            >
              Every response comes back cited, graded, and labelled with the
              skill that produced it - or it comes back empty.
            </p>
            <div data-reveal>
              <Link
                href="/app"
                data-magnetic
                className="group inline-flex items-center gap-2.5 rounded-full bg-canvas px-8 py-4 text-sm text-ink transition-all duration-300 hover:gap-4"
              >
                Open the agent
                <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
