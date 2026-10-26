"use client";

import { SplitText } from "./SplitText";

/** The three shipped skills, matching skills/ in the repository root. */
const SKILLS = [
  {
    name: "find-precedent",
    description:
      "Locates prior agreements containing a comparable clause and summarises how the position was resolved.",
    example: "Show me governing law clauses from prior merger agreements",
  },
  {
    name: "negotiation-check",
    description:
      "Surfaces where a draft clause diverges from the firm's historical negotiating position.",
    example: "Does this indemnity match what we accepted last quarter?",
  },
  {
    name: "risk-flag",
    description:
      "Reviews a clause set against the firm's own standards and returns a graded readout with reasons.",
    example: "Flag the risky terms in this vendor agreement",
  },
];

export function Skills() {
  return (
    <section id="skills" className="py-28 md:py-40">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid lg:grid-cols-[1fr_1.15fr] gap-14 lg:gap-20 items-start">
          <div className="lg:sticky lg:top-32">
            <p data-reveal className="text-[11px] font-mono uppercase tracking-[0.2em] text-ink-40 mb-5">
              Agent Skills
            </p>
            <SplitText
              as="h2"
              text="Capabilities are files, not branches."
              className="text-[clamp(2rem,4.5vw,3.25rem)] font-medium leading-[1.05] tracking-[-0.025em] block mb-6"
            />
            <p data-reveal className="text-lg text-ink-60 leading-relaxed mb-8">
              Each skill is a folder containing one <code className="font-mono text-[0.9em] px-1.5 py-0.5 rounded bg-sand">SKILL.md</code>.
              The harness reads them at runtime and routes between them generically.
            </p>
            <p data-reveal className="text-ink-60 leading-relaxed text-[15px]">
              A fourth skill is a new folder, not a new code path. The UI surfaces
              which one ran, so the routing decision is visible rather than implied.
            </p>
          </div>

          <div data-reveal-group className="flex flex-col gap-4">
            {SKILLS.map((skill) => (
              <article
                key={skill.name}
                data-reveal-item
                className="hover-lift border border-sand-deep bg-paper p-7 md:p-8"
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-2 h-2 rounded-full bg-ink" />
                  <h3 className="font-mono text-[13px] tracking-tight">
                    {skill.name}
                  </h3>
                </div>
                <p className="text-ink-60 leading-relaxed mb-5 text-[15px]">
                  {skill.description}
                </p>
                <p className="font-mono text-[12.5px] text-ink-40 border-l-2 border-sand-deep pl-4">
                  {skill.example}
                </p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}