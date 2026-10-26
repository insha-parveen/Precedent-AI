"use client";

import { Clause, DocumentResponse } from "@/types/api";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { useEffect, useState } from "react";

interface DocumentDrawerProps {
  document: DocumentResponse | null;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentDrawer({
  document: doc,
  isOpen,
  onClose,
}: DocumentDrawerProps) {
  useEffect(() => {
    if (isOpen) {
      window.document.body.style.overflow = "hidden";
    } else {
      window.document.body.style.overflow = "unset";
    }
    return () => {
      window.document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen || !doc) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/30 animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div className="flex-1 max-w-2xl bg-white shadow-2xl animate-slide-in-right flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-sand-deep">
          <div>
            <h3 className="font-serif text-lg font-semibold text-ink">
              {doc.doc_title}
            </h3>
            <div className="flex items-center gap-3 mt-1 text-sm text-ink-60">
              <span className="px-2 py-0.5 bg-sand rounded text-ink-60">
                {doc.source}
              </span>
              {doc.doc_type && (
                <span className="px-2 py-0.5 bg-sand rounded text-ink-60">
                  {doc.doc_type}
                </span>
              )}
              {doc.jurisdiction && (
                <span className="px-2 py-0.5 bg-sand rounded text-ink-60">
                  {doc.jurisdiction}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-sand transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5 text-ink-60" />
          </button>
        </div>

        {/* Metadata */}
        <div className="p-4 border-b border-sand-deep bg-canvas">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {doc.parties.length > 0 && (
              <div className="col-span-2">
                <p className="font-medium text-ink">Parties</p>
                <p className="text-ink-60">{doc.parties.join(", ")}</p>
              </div>
            )}
            {doc.filing_date && (
              <div>
                <p className="font-medium text-ink">Filing Date</p>
                <p className="text-ink-60">{doc.filing_date}</p>
              </div>
            )}
          </div>
        </div>

        {/* Clauses */}
        <div className="flex-1 overflow-y-auto p-4">
          {doc.clauses.length === 0 ? (
            <p className="text-ink-60 text-center py-8">
              No clauses available for this document.
            </p>
          ) : (
            <div className="space-y-4">
              {doc.clauses.map((clause: Clause) => (
                <ClauseCard key={clause.clause_id} clause={clause} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ClauseCard({ clause }: { clause: Clause }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-sand-deep rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between bg-canvas hover:bg-sand transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="px-2 py-1 bg-ink/10 text-ink text-xs font-mono rounded">
            Clause {clause.clause_id}
          </span>
          {clause.clause_type && (
            <span className="px-2 py-1 bg-sand text-ink text-xs rounded font-medium">
              {clause.clause_type}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-ink-60" />
        ) : (
          <ChevronDown className="w-5 h-5 text-ink-60" />
        )}
      </button>
      {expanded && (
        <div className="p-4 border-t border-sand-deep bg-white">
          <pre className="font-serif text-sm text-ink whitespace-pre-wrap leading-relaxed">
            {clause.clause_text}
          </pre>
        </div>
      )}
    </div>
  );
}
