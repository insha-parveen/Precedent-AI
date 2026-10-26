"use client";

import ReactMarkdown from "react-markdown";
import { CitationChip } from "./CitationChip";
import { RiskCard } from "./RiskCard";

interface MarkdownRendererProps {
  content: string;
  onCitationClick: (docId: number) => void;
}

export function MarkdownRenderer({
  content,
  onCitationClick,
}: MarkdownRendererProps) {
  // Pre-process content to extract risk readouts
  const { markdown, riskReadouts } = extractRiskReadouts(content);

  return (
    <div className="prose prose-neutral max-w-none">
      {/* Render risk cards first if present */}
      {riskReadouts.map((risk, index) => (
        <RiskCard key={index} {...risk} />
      ))}

      {/* Render main markdown content with custom components */}
      <ReactMarkdown
        components={{
          // Override inline code to handle citations
          code: ({ children, ...props }) => {
            const text =
              typeof children === "string" ? children : String(children);
            const citationMatch = text.match(/^doc:(\d+)$/);
            if (citationMatch) {
              const docId = parseInt(citationMatch[1], 10);
              return <CitationChip docId={docId} onClick={onCitationClick} />;
            }
            return <code {...props}>{children}</code>;
          },
          // Style paragraph
          p: ({ children, ...props }) => (
            <p {...props} className="mb-4 leading-relaxed text-ink">
              {children}
            </p>
          ),
          // Style headings
          h1: ({ children, ...props }) => (
            <h1
              {...props}
              className="font-serif text-2xl font-bold text-ink mb-3 mt-6"
            >
              {children}
            </h1>
          ),
          h2: ({ children, ...props }) => (
            <h2
              {...props}
              className="font-serif text-xl font-semibold text-ink mb-2 mt-5"
            >
              {children}
            </h2>
          ),
          h3: ({ children, ...props }) => (
            <h3
              {...props}
              className="font-serif text-lg font-medium text-ink mb-2 mt-4"
            >
              {children}
            </h3>
          ),
          // Style lists
          ul: ({ children, ...props }) => (
            <ul
              {...props}
              className="list-disc list-inside mb-4 space-y-1 text-ink"
            >
              {children}
            </ul>
          ),
          ol: ({ children, ...props }) => (
            <ol
              {...props}
              className="list-decimal list-inside mb-4 space-y-1 text-ink"
            >
              {children}
            </ol>
          ),
          li: ({ children, ...props }) => (
            <li {...props} className="ml-4">
              {children}
            </li>
          ),
          // Style blockquote
          blockquote: ({ children, ...props }) => (
            <blockquote
              {...props}
              className="border-l-4 border-ink pl-4 italic text-ink-60 my-4"
            >
              {children}
            </blockquote>
          ),
          // Style horizontal rule
          hr: ({ ...props }) => (
            <hr {...props} className="border-sand-deep my-6" />
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}

interface RiskReadout {
  level: "low" | "medium" | "high";
  reason: string;
}

function extractRiskReadouts(content: string): {
  markdown: string;
  riskReadouts: RiskReadout[];
} {
  const riskReadouts: RiskReadout[] = [];
  const riskPattern =
    /Risk:\s*(Low|Medium|High)\s*\n\s*Reason:\s*([^\n]+(?:\n(?!\n)[^\n]+)*)/gi;

  let markdown = content;
  let match;

  while ((match = riskPattern.exec(content)) !== null) {
    const level = match[1].toLowerCase() as "low" | "medium" | "high";
    const reason = match[2].trim();
    riskReadouts.push({ level, reason });
  }

  // Remove risk readouts from markdown content to avoid duplication
  markdown = markdown.replace(riskPattern, "").trim();

  return { markdown, riskReadouts };
}
