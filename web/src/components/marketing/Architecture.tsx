"use client";

import { SplitText } from "./SplitText";

/** Architecture pipeline: the five stages every query passes through. */
const PIPELINE = [
  {
    step: "01",
    title: "Query arrives",
    body: "One question in - a contract review, a precedent request, a risk check. No dashboard, no query builder.",
  },
  {
    step: "02",
    title: "Skill routing",
    body: "The agent loads the available SKILL.md files and picks the pipeline that fits, from instructions rather than a hardcoded branch.",
  },
  {
    step: "03",
    title: "Permissioned retrieval",
    body: "Hybrid search runs against pgvector and full-text, filtered on access_group at every step.",
  },
  {
    step: "04",
    title: "Verification",
    body: "A verifying pass checks each claim against the retrieved clauses. Unsupported claims are dropped here, not hidden in the prompt.",
  },
  {
    step: "05",
    title: "Grounded answer",
    body: "What returns is synthesised, cites its sources inline, and is labelled with the skill that produced it.",
  },
];

export function Architecture() {
  return (
    <section id="architecture" className="py-28 md:py-40 bg-ink text-canvas">
      <div className="max-w-7xl mx-auto px-6">
        <div className="max-w-2xl mb-20">
          <p
            data-reveal
            className="text-[11px] font-mono uppercase tracking-[0.2em] text-canvas/40 mb-5"
          >
            How it works
          </p>
          <SplitText
            as="h2"
            text="Five stages, every single time."
            className="text-[clamp(2rem,4.5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.025em] block mb-6"
          />
          <p data-reveal className="text-lg text-canvas/60 leading-relaxed">
            The same harness serves the web UI and the MCP server, so a Claude
            Desktop session and the chat UI both get the same guarantees.
          </p>
        </div>

        <div
          data-reveal-group
          className="grid gap-px bg-canvas/15 border border-canvas/15"
        >
          {PIPELINE.map((stage) => (
            <div
              key={stage.step}
              data-reveal-item
              data-pipeline-row
              className="group grid md:grid-cols-[100px_1fr_1.4fr] gap-6 md:gap-10 bg-ink p-8 md:p-10 transition-colors duration-500 hover:bg-ink-light"
            >
              <span
                data-step-num
                className="font-mono text-sm text-canvas/30 transition-colors duration-500 group-hover:text-canvas/70"
              >
                {stage.step}
              </span>
              <h3 className="text-xl font-medium tracking-tight leading-snug">
                {stage.title}
              </h3>
              <p className="text-canvas/60 leading-relaxed text-[15px] md:pt-1">
                {stage.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
