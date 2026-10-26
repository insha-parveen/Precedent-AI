"use client";

import Link from "next/link";

const FOOTER_COLUMNS = [
  {
    heading: "Product",
    links: [
      { label: "AI Workflows", href: "/#workflows" },
      { label: "Enterprise Search", href: "/#workflows" },
      { label: "Knowledge Graph", href: "/#knowledge" },
      { label: "Platform Architecture", href: "/#platform" },
    ],
  },
  {
    heading: "Platform",
    links: [
      { label: "Open Agent App", href: "/app" },
      { label: "Model Context Protocol", href: "/#platform" },
      { label: "Benchmark Evaluation", href: "/#stats" },
      { label: "Insights & Blog", href: "/#insights" },
    ],
  },
  {
    heading: "Ecosystem",
    links: [
      {
        label: "GitHub Repository",
        href: "https://github.com/insha-parveen/Precedent-AI",
      },
      { label: "CUAD Dataset", href: "https://www.atticusprojectai.org/cuad" },
      { label: "SEC EDGAR Ingestion", href: "https://www.sec.gov/edgar" },
      { label: "Claude Agent SDK", href: "https://claude.ai" },
    ],
  },
];

export function Footer() {
  return (
    <footer id="footer" className="border-t border-sand-deep py-20 bg-canvas">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid gap-12 md:grid-cols-[1.5fr_repeat(3,1fr)] mb-16">
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-7 h-7 rounded-full bg-ink flex items-center justify-center text-canvas font-serif font-bold text-xs">
                P
              </div>
              <span className="text-lg font-serif font-normal tracking-tight text-ink">
                Precedent
              </span>
            </div>
            <p className="text-sm text-ink-60 leading-relaxed max-w-xs font-sans">
              Retrieval-first contract intelligence. Transforming institutional
              legal data and SEC filings into structured, permission-aware AI
              workflows.
            </p>
          </div>

          {FOOTER_COLUMNS.map((column) => (
            <div key={column.heading}>
              <h3 className="text-[11px] font-mono uppercase tracking-[0.18em] text-ink-40 mb-5 font-semibold">
                {column.heading}
              </h3>
              <ul className="flex flex-col gap-3">
                {column.links.map((link) => {
                  const isExternal = link.href.startsWith("http");
                  return (
                    <li key={link.label}>
                      {isExternal ? (
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="link-underline text-xs font-sans text-ink-60 hover:text-ink transition-colors duration-300"
                        >
                          {link.label}
                        </a>
                      ) : (
                        <Link
                          href={link.href}
                          className="link-underline text-xs font-sans text-ink-60 hover:text-ink transition-colors duration-300"
                        >
                          {link.label}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-8 border-t border-sand-deep text-xs font-mono text-ink-40">
          <p>
            Retrieval before generation. Citation or refuse. Permissions always.
          </p>
          <p>
            Corpus: 510+ Contracts (CUAD) &middot; SEC EDGAR &middot; pgvector
          </p>
        </div>
      </div>
    </footer>
  );
}
