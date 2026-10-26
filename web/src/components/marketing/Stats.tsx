"use client";

import { SplitText } from "./SplitText";

/**
 * Section 7 from DeepJudge:
 * - Headline: "Trusted by exceptional lawyers at the world's top firms and in-house teams"
 * - 5-column metric cards (+65%, +85%, +23, +4x ROI, 90%)
 * - Logo ticker bar: "Trusted by the world's top legal teams"
 */
const METRICS = [
  {
    prefix: "+",
    value: 65,
    suffix: "%",
    label: "Saved per user / per year searching",
    note: "Measurable legal workflow time",
  },
  {
    prefix: "+",
    value: 85,
    suffix: "%",
    label: "Adoption in under two months",
    note: "Across corporate and practice groups",
  },
  {
    prefix: "+",
    value: 23,
    suffix: "",
    label: "Queries including 10+ AI Workflows",
    note: "Per active user per day",
  },
  {
    prefix: "+",
    value: 4,
    suffix: "x ROI",
    label: "In the first year",
    note: "Quantified deal velocity",
  },
  {
    prefix: "",
    value: 90,
    suffix: "%",
    label: "Find results faster than prior tools",
    note: "Verified in practitioner benchmark",
  },
];

const LOGOS = [
  "HOMBURGER",
  "CMS LEGAL",
  "LEXR",
  "GREENBERG TRAURIG",
  "ATTICUS PROJECT",
  "SEC EDGAR",
  "CLIFFORD CHANCE",
  "LATHAM & WATKINS",
];

export function Stats() {
  return (
    <section id="stats" className="py-24 md:py-36 border-t border-sand-deep/60 bg-canvas">
      <div className="max-w-7xl mx-auto px-6">
        {/* Editorial Heading */}
        <div className="max-w-3xl mb-16">
          <SplitText
            as="h2"
            text="Trusted by exceptional lawyers at the world's top firms and in-house teams"
            className="text-[clamp(2.15rem,4vw,3.25rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block"
          />
        </div>

        {/* 5-Column Metrics Grid matching DeepJudge */}
        <div
          data-reveal-group
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-px bg-sand-deep border border-sand-deep mb-24 rounded-2xl overflow-hidden shadow-xs"
        >
          {METRICS.map((stat, i) => (
            <div
              key={i}
              data-reveal-item
              className="bg-canvas p-6 sm:p-7 flex flex-col justify-between hover:bg-paper transition-colors duration-300"
            >
              <div>
                <div className="flex items-baseline mb-3 text-ink">
                  {stat.prefix && (
                    <span className="font-serif text-3xl sm:text-4xl font-light">
                      {stat.prefix}
                    </span>
                  )}
                  <span
                    data-counter
                    data-counter-to={stat.value}
                    data-counter-decimals="0"
                    className="font-serif text-4xl sm:text-5xl font-light tracking-tight leading-none"
                  >
                    {stat.value}
                  </span>
                  {stat.suffix && (
                    <span className="font-serif text-2xl sm:text-3xl font-light ml-0.5">
                      {stat.suffix}
                    </span>
                  )}
                </div>
                <p className="text-xs sm:text-sm font-sans font-medium text-ink leading-snug mb-1">
                  {stat.label}
                </p>
              </div>
              <p className="text-[11px] font-mono text-ink-40 mt-3 pt-3 border-t border-sand">
                {stat.note}
              </p>
            </div>
          ))}
        </div>

        {/* Logo Bar Section */}
        <div data-reveal className="text-center pt-8 border-t border-sand-deep/60">
          <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-ink-40 mb-8">
            Trusted by the world&apos;s top legal teams
          </p>

          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-14 opacity-60">
            {LOGOS.map((name, i) => (
              <span
                key={i}
                className="font-serif tracking-widest text-xs md:text-sm font-semibold text-ink uppercase hover:opacity-100 transition-opacity cursor-default"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
