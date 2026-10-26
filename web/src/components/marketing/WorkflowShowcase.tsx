"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, Sparkles } from "lucide-react";
import { SplitText } from "./SplitText";

/**
 * Section 4 & 5 from DeepJudge:
 * - Philosophy transition: "Finding the right information... Build, deploy and orchestrate AI agents"
 * - Two-column workflow showcase: "Automate mission-critical workflows with ease"
 * - Interactive modular cards: "Arbitration Request", "Summarize a Matter",
 *   "My Custom AI Workflow" (highlighted lilac card), "Create a Closing Checklist".
 */
export function WorkflowShowcase() {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>("custom");

  return (
    <section id="workflows" className="py-24 md:py-36 border-t border-sand-deep/60 relative">
      <div className="max-w-7xl mx-auto px-6">
        {/* Transitional Header */}
        <div className="text-center max-w-3xl mx-auto mb-20 md:mb-28">
          <p data-reveal className="text-[12px] font-mono uppercase tracking-[0.2em] text-ink-40 mb-5">
            Finding the right information is the beginning of every workflow
          </p>
          <SplitText
            as="h2"
            text="Build, deploy and orchestrate AI agents powered by your data"
            className="text-[clamp(2.25rem,4.5vw,3.75rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block mb-6"
          />
          <p data-reveal className="text-base md:text-lg text-ink-60 font-sans leading-relaxed">
            Empower your legal apps and agents with AI Workflows that work like you do
            and know what your firm knows.
          </p>
        </div>

        {/* Two-Column Workflow Builder Section */}
        <div className="grid lg:grid-cols-[1fr_1.35fr] gap-12 lg:gap-16 items-center">
          {/* Left Column Copy */}
          <div>
            <p data-reveal className="text-[11px] font-mono uppercase tracking-[0.2em] text-violet mb-4 font-semibold">
              Precedent AI Workflows
            </p>
            <SplitText
              as="h3"
              text="Automate mission-critical workflows with ease"
              className="text-[clamp(2rem,3.75vw,3.25rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block mb-6"
            />
            <p data-reveal className="text-base text-ink-60 leading-relaxed font-sans mb-8">
              Precedent AI Workflows enable building, deploying, orchestrating, and
              governing AI agents to drive real ROI. Our LLM-agnostic agentic reasoning
              executes complex, multi-step tasks—combining data from multiple sources
              and taking actions to get work done with transparency and precision.
            </p>

            {/* Workflow selector pills */}
            <div data-reveal className="flex flex-col gap-3 mb-8">
              <button
                onClick={() => setSelectedWorkflow("custom")}
                className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all duration-300 ${
                  selectedWorkflow === "custom"
                    ? "bg-paper border-violet shadow-sm"
                    : "bg-canvas border-sand-deep hover:bg-paper/60"
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-violet" />
                    <span className="font-medium text-sm text-ink">My Custom AI Workflow</span>
                  </div>
                  <p className="text-xs text-ink-60 mt-1 pl-4">
                    Orchestrated multi-step agent with verified citations
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-violet" />
              </button>

              <button
                onClick={() => setSelectedWorkflow("arbitration")}
                className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all duration-300 ${
                  selectedWorkflow === "arbitration"
                    ? "bg-paper border-violet shadow-sm"
                    : "bg-canvas border-sand-deep hover:bg-paper/60"
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-ink" />
                    <span className="font-medium text-sm text-ink">Arbitration Request</span>
                  </div>
                  <p className="text-xs text-ink-60 mt-1 pl-4">
                    Dispute resolution & governing law cross-referencing
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-ink-40" />
              </button>

              <button
                onClick={() => setSelectedWorkflow("checklist")}
                className={`flex items-center justify-between p-4 rounded-2xl border text-left transition-all duration-300 ${
                  selectedWorkflow === "checklist"
                    ? "bg-paper border-violet shadow-sm"
                    : "bg-canvas border-sand-deep hover:bg-paper/60"
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-ink" />
                    <span className="font-medium text-sm text-ink">Create a Closing Checklist</span>
                  </div>
                  <p className="text-xs text-ink-60 mt-1 pl-4">
                    Automated conditions precedent & disclosure schedules
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-ink-40" />
              </button>
            </div>

            <div data-reveal>
              <Link
                href="/app"
                data-magnetic
                className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-medium text-canvas transition-transform duration-300 hover:scale-[1.02]"
              >
                <span>Deploy a workflow</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Right Column Canvas with Floating UI Cards matching DeepJudge */}
          <div
            data-reveal
            className="relative min-h-[460px] md:min-h-[540px] rounded-3xl bg-sand/40 border border-sand-deep p-6 sm:p-10 flex flex-col justify-between overflow-hidden shadow-inner"
          >
            {/* Top Row Cards */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="bg-paper rounded-2xl border border-sand-deep p-4 shadow-sm max-w-xs transition-transform duration-300 hover:-translate-y-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-risk-medium" />
                  <span className="text-xs font-mono uppercase tracking-wider text-ink-60">
                    Arbitration Request
                  </span>
                </div>
                <p className="text-xs text-ink-60 font-sans">
                  Extracts dispute resolution clauses & compares ICC vs LCIA forums.
                </p>
              </div>

              <div className="bg-paper rounded-2xl border border-sand-deep p-4 shadow-sm max-w-xs transition-transform duration-300 hover:-translate-y-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-violet" />
                  <span className="text-xs font-mono uppercase tracking-wider text-ink-60">
                    Summarize a Matter
                  </span>
                </div>
                <p className="text-xs text-ink-60 font-sans">
                  Synthesizes 40+ transaction exhibits into an executive memorandum.
                </p>
              </div>
            </div>

            {/* Center Prominent Card: "My Custom AI Workflow" (Signature Lilac card from screenshot) */}
            <div className="relative my-4 self-center w-full max-w-md bg-lilac/70 border border-lavender-border rounded-3xl p-6 sm:p-7 shadow-[0_12px_40px_rgba(124,58,237,0.12)] transition-all duration-300 hover:shadow-[0_16px_48px_rgba(124,58,237,0.18)]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-xl bg-violet flex items-center justify-center text-white">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-ink">My Custom AI Workflow</h4>
                    <span className="text-[10px] font-mono text-ink-60 uppercase">
                      LangGraph · 5 Stages
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-paper/80 border border-violet-light/50 text-violet font-semibold">
                  ACTIVE
                </span>
              </div>

              {/* Workflow Pipeline Steps */}
              <div className="grid grid-cols-3 gap-2 bg-paper/90 rounded-2xl p-3 border border-sand-deep/60 text-center mb-4">
                <div className="p-2 rounded-xl bg-canvas">
                  <span className="block text-[10px] font-mono uppercase text-ink-40">Input</span>
                  <span className="text-xs font-medium text-ink">Search Query</span>
                </div>
                <div className="p-2 rounded-xl bg-lavender border border-violet-light/40">
                  <span className="block text-[10px] font-mono uppercase text-violet font-semibold">
                    Retrieve
                  </span>
                  <span className="text-xs font-medium text-ink">pgvector + BM25</span>
                </div>
                <div className="p-2 rounded-xl bg-canvas">
                  <span className="block text-[10px] font-mono uppercase text-ink-40">Results</span>
                  <span className="text-xs font-medium text-ink">Grounded</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-ink-60 font-mono">
                <span className="flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5 text-risk-low" />
                  Citation checked
                </span>
                <span className="text-violet font-semibold text-[11px]">Sub-250ms</span>
              </div>
            </div>

            {/* Bottom Row Cards */}
            <div className="flex flex-col sm:flex-row items-end justify-between gap-4">
              <div className="bg-paper rounded-2xl border border-sand-deep p-4 shadow-sm max-w-xs transition-transform duration-300 hover:-translate-y-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-ink" />
                  <span className="text-xs font-mono uppercase tracking-wider text-ink-60">
                    Closing Checklist
                  </span>
                </div>
                <p className="text-xs text-ink-60 font-sans">
                  Extracts all covenants and regulatory consents required prior to closing.
                </p>
              </div>

              <div className="bg-paper rounded-2xl border border-sand-deep p-4 shadow-sm max-w-xs transition-transform duration-300 hover:-translate-y-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-risk-low" />
                  <span className="text-xs font-mono uppercase tracking-wider text-ink-60">
                    Secure Chat & MCP
                  </span>
                </div>
                <p className="text-xs text-ink-60 font-sans">
                  Stdio transport for Claude Desktop with strict permission boundaries.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
