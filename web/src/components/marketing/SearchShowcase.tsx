"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Search, ShieldCheck } from "lucide-react";
import { SplitText } from "./SplitText";

const SAMPLE_QUERIES = [
  "Have we done a deal with an uncapped indemnity in Delaware?",
  "What is our standard non-solicitation term in cross-border tech acquisitions?",
  "Show me precedent governing law clauses under English law with LCIA arbitration",
  "Which agreements contain unilateral termination for convenience without penalty?",
];

/**
 * Section 2 from DeepJudge:
 * - Headline: "The only AI platform that knows everything your firm knows"
 * - Subtext on the right
 * - Wide lavender/violet slat matrix canvas
 * - Centered floating search bar pill with typewriter query and interactive result card
 */
export function SearchShowcase() {
  const [queryIndex, setQueryIndex] = useState(0);
  const [displayText, setDisplayText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  // Typewriter effect cycling through realistic legal precedent queries
  useEffect(() => {
    if (hasInteracted) return;

    const fullText = SAMPLE_QUERIES[queryIndex];
    const typingSpeed = isDeleting ? 25 : 45;

    const timer = setTimeout(() => {
      if (!isDeleting) {
        if (displayText.length < fullText.length) {
          setDisplayText(fullText.slice(0, displayText.length + 1));
        } else {
          // Pause before deleting
          setTimeout(() => setIsDeleting(true), 3200);
        }
      } else {
        if (displayText.length > 0) {
          setDisplayText(fullText.slice(0, displayText.length - 1));
        } else {
          setIsDeleting(false);
          setQueryIndex((prev) => (prev + 1) % SAMPLE_QUERIES.length);
        }
      }
    }, typingSpeed);

    return () => clearTimeout(timer);
  }, [displayText, isDeleting, queryIndex, hasInteracted]);

  return (
    <section className="py-24 md:py-36 border-t border-sand-deep/60 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        {/* Two-column header */}
        <div className="grid md:grid-cols-[1.3fr_1fr] gap-8 md:gap-16 items-start mb-16">
          <div>
            <SplitText
              as="h2"
              text="The only AI platform that knows everything your firm knows"
              className="text-[clamp(2.25rem,4.5vw,3.75rem)] font-serif font-normal leading-[1.06] tracking-[-0.03em] text-ink block"
            />
          </div>
          <div data-reveal className="md:pt-3">
            <p className="text-base md:text-lg text-ink-60 leading-relaxed font-sans">
              Unlocking comprehensive enterprise search across every matter, contract,
              and filing to empower all areas of your legal operations with instant,
              governed precision.
            </p>
          </div>
        </div>

        {/* Slats Matrix with Centered Search Bar */}
        <div
          data-reveal
          className="relative rounded-3xl bg-lavender/50 border border-lavender-border/70 p-6 sm:p-12 md:p-16 overflow-hidden shadow-[0_4px_30px_rgba(124,58,237,0.03)]"
        >
          {/* Lavender/violet slats background matrix */}
          <div
            className="absolute inset-0 flex items-center justify-between px-4 sm:px-8 opacity-45 pointer-events-none select-none overflow-hidden"
            aria-hidden="true"
          >
            {Array.from({ length: 64 }).map((_, i) => {
              // Rhythmic heights creating a wave across the search container
              const sinVal = Math.sin((i / 64) * Math.PI * 4);
              const height = Math.floor(35 + (sinVal + 1) * 28);
              const isAccent = i % 7 === 0 || i === 23 || i === 41;
              return (
                <div
                  key={i}
                  className={`w-[2.5px] rounded-full transition-all duration-500 ${
                    isAccent
                      ? "bg-violet-light/80 shadow-[0_0_8px_rgba(139,92,246,0.5)]"
                      : "bg-violet/25"
                  }`}
                  style={{ height: `${height}%` }}
                />
              );
            })}
          </div>

          {/* Centered Floating Search Interface */}
          <div className="relative z-10 max-w-2xl mx-auto my-6 sm:my-10">
            <div className="relative flex items-center bg-paper rounded-full border border-sand-deep/80 shadow-[0_8px_32px_rgba(24,24,22,0.08)] p-2 sm:p-2.5 transition-all duration-300 focus-within:border-violet-light focus-within:shadow-[0_8px_32px_rgba(124,58,237,0.14)]">
              <div className="pl-4 sm:pl-5 pr-3 text-ink-40">
                <Search className="w-5 h-5 text-violet" />
              </div>

              <input
                type="text"
                value={displayText}
                onChange={(e) => {
                  setHasInteracted(true);
                  setDisplayText(e.target.value);
                }}
                placeholder="Ask or search across all indexed contracts..."
                className="w-full bg-transparent text-sm sm:text-base font-sans text-ink placeholder:text-ink-40 focus:outline-none pr-3"
              />

              <Link
                href="/app"
                className="shrink-0 inline-flex items-center gap-1.5 rounded-full bg-ink px-5 sm:px-6 py-2.5 sm:py-3 text-xs sm:text-sm font-medium tracking-wide text-canvas uppercase transition-all duration-300 hover:bg-violet hover:scale-[1.02]"
              >
                <span>SEARCH</span>
              </Link>
            </div>

            {/* Grounded Result Preview Pill */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3 px-3 py-2.5 rounded-2xl bg-paper/90 border border-sand-deep text-xs font-mono text-ink-60 backdrop-blur-sm shadow-sm animate-fade-in">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-low" />
                <span className="font-semibold text-ink">Grounded Precedent:</span>
                <span className="truncate max-w-[280px] sm:max-w-[340px]">
                  [doc:1048] Delaware M&A Agreement · §14.2
                </span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-ink-40">
                <ShieldCheck className="w-3.5 h-3.5 text-risk-low" />
                <span>Verified in CUAD Corpus</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
