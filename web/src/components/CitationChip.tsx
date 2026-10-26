"use client";

import { FileText } from "lucide-react";
import { useState } from "react";

interface CitationChipProps {
  docId: number;
  onClick: (docId: number) => void;
}

export function CitationChip({ docId, onClick }: CitationChipProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={() => onClick(docId)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        inline-flex items-center gap-1 px-2 py-0.5 rounded border transition-all duration-150
        bg-citation-bg border-citation-border text-ink
        hover:bg-citation-hover hover:border-ink
        cursor-pointer select-none whitespace-nowrap
        text-sm font-mono
      `}
      aria-label={`View document ${docId}`}
    >
      <FileText className="w-3 h-3" />
      <span>doc:{docId}</span>
      {isHovered && <span className="text-ink">â†’</span>}
    </button>
  );
}
