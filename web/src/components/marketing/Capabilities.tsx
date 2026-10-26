"use client";

import { Database, GitBranch, Network, ShieldCheck } from "lucide-react";
import { SplitText } from "./SplitText";

const CAPABILITIES = [
  {
    icon: Network,
    label: "Hybrid Retrieval",
    title: "Semantic and keyword, at the same time",
    body: "Contract questions rarely phrase themselves as keywords. Clause-aware chunking plus pgvector means a query for \u201cwhat can we not do after closing\u201d lands on the right clause even without shared vocabulary.",
  },
  {
    icon: ShieldCheck,
    label: "Permission-Aware",
    title: "Access control on every single query",
    body: "Every row carries an access_group and every retrieval path filters on it. In this demo the corpus is public, but the enforcement is real rather than assumed - see ADR-009.",
  },
  {
    icon: GitBranch,
    label: "Skills as Data",
    title: "Behaviour lives in SKILL.md, not in code",
    body: "Adding a capability means writing a SKILL.md file. The agent loop only loads, routes and executes skills generically - there is no branching on skill names anywhere in the codebase.",
  },
  {
    icon: Database,
    label: "Grounded by Default",
    title: "Citation or refuse, enforced in code",
    body: "A check runs before any answer leaves the harness. Ungrounded claims are blocked before the user sees them, which is why the UI can show a grounded/not-grounded verdict honestly.",
  },
];

export function Capabilities() {
  return (
    <section id="capabilities" className="py-28 md:py-40">
      <div className="max-w-7xl mx-auto px-6">
        <div className="max-w-2xl mb-16">
          <p
            data-reveal
            className="text-[11px] font-mono uppercase tracking-[0.2em] text-ink-40 mb-5"
          >
            What it does
          </p>
          <SplitText
            as="h2"
            text="An index first. A model second."
            className="text-[clamp(2rem,4.5vw,3.5rem)] font-medium leading-[1.05] tracking-[-0.025em] block mb-6"
          />
          <p data-reveal className="text-lg text-ink-60 leading-relaxed">
            Most legal AI bolts retrieval onto a chat model as an occasional
            lookup. Precedent treats it as an always-on layer that every answer
            passes through.
          </p>
        </div>

        <div
          data-reveal-group
          className="grid sm:grid-cols-2 gap-px bg-sand-deep border border-sand-deep"
        >
          {CAPABILITIES.map((item) => {
            const Icon = item.icon;
            return (
              <article
                key={item.label}
                data-reveal-item
                className="hover-lift group bg-canvas p-8 md:p-10"
              >
                <div className="flex items-center gap-3 mb-6">
                  <span className="flex items-center justify-center w-10 h-10 rounded-full border border-sand-deep bg-paper transition-colors duration-500 group-hover:border-ink">
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="text-[11px] font-mono uppercase tracking-[0.16em] text-ink-40">
                    {item.label}
                  </span>
                </div>
                <h3 className="text-xl font-medium tracking-tight mb-3 leading-snug">
                  {item.title}
                </h3>
                <p className="text-ink-60 leading-relaxed text-[15px]">
                  {item.body}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
