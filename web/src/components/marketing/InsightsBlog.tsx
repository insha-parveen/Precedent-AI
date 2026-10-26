"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { SplitText } from "./SplitText";

/**
 * Section 9 from DeepJudge:
 * - Header: "Insights from our blog" + "VIEW ALL" button
 * - 3 distinctive pastel-tinted cards matching the screenshot:
 *   1. Warm Tan card (#e9e3da)
 *   2. Soft Lavender card (#e5def3)
 *   3. Off-white Cream card (#f6f4f0)
 */
const POSTS = [
  {
    bg: "bg-[#e9e3da]",
    border: "border-[#d8d0c4]",
    tag: "INTEGRATIONS",
    title: "Precedent + Enterprise: Institutional Intelligence for Every Workflow",
    excerpt:
      "Bridging the gap between institutional document repositories and LLM-powered reasoning to empower corporate legal and law firm workflows.",
    author: "Precedent Research",
    readTime: "4 min read",
  },
  {
    bg: "bg-[#e5def3]",
    border: "border-[#d4c9ec]",
    tag: "PRODUCT UPDATE",
    title: "Cross-Matter Intelligence: Evolving Legal Search into Decision-Ready Insights",
    excerpt:
      "Launching SuperSearch: extending pgvector hybrid retrieval to cross-reference multi-jurisdictional precedents in a single click.",
    author: "Core Architecture Team",
    readTime: "6 min read",
  },
  {
    bg: "bg-[#f6f4f0]",
    border: "border-[#e6e1d7]",
    tag: "PROTOCOL",
    title: "MCP Isn't Magic. It's Access.",
    excerpt:
      "Model Context Protocol doesn't make models smarter—it standardizes compliant access. How Precedent exposes contract tools to Claude Desktop.",
    author: "Engineering",
    readTime: "5 min read",
  },
];

export function InsightsBlog() {
  return (
    <section id="insights" className="py-24 md:py-36 bg-canvas border-t border-sand-deep/60">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-6 mb-16">
          <div>
            <SplitText
              as="h2"
              text="Insights from our blog"
              className="text-[clamp(2.25rem,4.5vw,3.75rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block"
            />
          </div>

          <div data-reveal>
            <Link
              href="/app"
              className="inline-flex items-center gap-2 rounded-full border border-sand-deep px-6 py-2.5 text-xs font-mono tracking-wider uppercase text-ink hover:bg-paper transition-colors duration-300"
            >
              <span>VIEW ALL</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-ink-60" />
            </Link>
          </div>
        </div>

        {/* 3 Pastel Cards Grid matching DeepJudge visual layout */}
        <div data-reveal-group className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {POSTS.map((post, idx) => (
            <article
              key={idx}
              data-reveal-item
              className={`group flex flex-col justify-between rounded-3xl p-8 sm:p-9 border ${post.bg} ${post.border} shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md cursor-pointer`}
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <span className="text-[10px] font-mono tracking-widest text-ink-60 uppercase font-semibold">
                    {post.tag}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-paper/60 flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                    <ArrowUpRight className="w-4 h-4 text-ink-60 group-hover:text-ink" />
                  </div>
                </div>

                <h3 className="font-serif text-xl sm:text-2xl font-normal text-ink leading-snug tracking-tight mb-4 group-hover:text-violet transition-colors duration-300">
                  {post.title}
                </h3>

                <p className="text-sm text-ink-60 font-sans leading-relaxed mb-8">
                  {post.excerpt}
                </p>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-ink/10 text-xs font-mono text-ink-60">
                <span>{post.author}</span>
                <span>{post.readTime}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
