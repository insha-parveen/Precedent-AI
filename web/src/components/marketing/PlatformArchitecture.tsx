"use client";

import { useState } from "react";
import { SplitText } from "./SplitText";
import {
  Search,
  Cpu,
  Layers,
  FileText,
  Mail,
  HardDrive,
  MessageSquare,
  Globe,
  Database,
  Lock,
  Sparkles,
} from "lucide-react";

type RoleTab = "users" | "agents" | "developers";

/**
 * Section 6 from DeepJudge:
 * "The one platform for your AI strategy"
 * - Role selector tabs: [Users] [Apps & Agents] [Developers]
 * - Stacked architectural diagram with DeepJudge Knowledge Search & Index at core
 * - Data sources row
 * - Side callout notes with hairline brackets
 */
export function PlatformArchitecture() {
  const [activeTab, setActiveTab] = useState<RoleTab>("agents");

  return (
    <section id="platform" className="py-24 md:py-36 bg-canvas border-t border-sand-deep/60 relative">
      <div className="max-w-6xl mx-auto px-6">
        {/* Centered Heading */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <SplitText
            as="h2"
            text="The one platform for your AI strategy"
            className="text-[clamp(2.25rem,4.5vw,3.75rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block mb-6"
          />

          {/* Role selector tabs matching DeepJudge top bar */}
          <div data-reveal className="inline-flex items-center gap-1 p-1 rounded-full bg-sand/70 border border-sand-deep">
            <button
              onClick={() => setActiveTab("users")}
              className={`px-5 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
                activeTab === "users"
                  ? "bg-paper text-ink shadow-xs"
                  : "text-ink-60 hover:text-ink"
              }`}
            >
              Users
            </button>
            <button
              onClick={() => setActiveTab("agents")}
              className={`px-5 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
                activeTab === "agents"
                  ? "bg-paper text-ink shadow-xs"
                  : "text-ink-60 hover:text-ink"
              }`}
            >
              Apps & Agents
            </button>
            <button
              onClick={() => setActiveTab("developers")}
              className={`px-5 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
                activeTab === "developers"
                  ? "bg-paper text-ink shadow-xs"
                  : "text-ink-60 hover:text-ink"
              }`}
            >
              Developers & IT
            </button>
          </div>
        </div>

        {/* Stacked Architecture Diagram */}
        <div
          data-reveal
          className="relative max-w-4xl mx-auto grid md:grid-cols-[1fr_260px] gap-8 items-center"
        >
          {/* Main Diagram Stack Container */}
          <div className="bg-paper rounded-3xl border border-sand-deep p-6 sm:p-8 shadow-sm flex flex-col gap-3">
            {/* Top Brand Tag */}
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-full bg-violet" />
              <span className="text-xs font-mono font-semibold tracking-widest uppercase text-ink">
                PREDENT PLATFORM
              </span>
            </div>

            {/* Layer 1: Applications Tier */}
            <div className="grid grid-cols-3 gap-2.5">
              <div
                className={`p-3.5 rounded-xl text-center border transition-all duration-300 ${
                  activeTab === "users"
                    ? "bg-violet text-white border-violet shadow-sm"
                    : "bg-lavender/60 border-lavender-border text-ink"
                }`}
              >
                <Search className="w-4 h-4 mx-auto mb-1.5 opacity-80" />
                <span className="text-xs font-semibold block">Search UI</span>
                <span className="text-[10px] opacity-75 font-sans">Natural Query</span>
              </div>

              <div
                className={`p-3.5 rounded-xl text-center border transition-all duration-300 ${
                  activeTab === "agents"
                    ? "bg-violet text-white border-violet shadow-sm"
                    : "bg-lavender/60 border-lavender-border text-ink"
                }`}
              >
                <Cpu className="w-4 h-4 mx-auto mb-1.5 opacity-80" />
                <span className="text-xs font-semibold block">AI Workflows</span>
                <span className="text-[10px] opacity-75 font-sans">Agent Skills</span>
              </div>

              <div
                className={`p-3.5 rounded-xl text-center border transition-all duration-300 ${
                  activeTab === "developers"
                    ? "bg-violet text-white border-violet shadow-sm"
                    : "bg-lavender/60 border-lavender-border text-ink"
                }`}
              >
                <Layers className="w-4 h-4 mx-auto mb-1.5 opacity-80" />
                <span className="text-xs font-semibold block">MCP Protocol</span>
                <span className="text-[10px] opacity-75 font-sans">Claude Tools</span>
              </div>
            </div>

            {/* Layer 2: Core Engine (Precedent Knowledge Search & Index) */}
            <div className="p-4 rounded-2xl bg-lilac/80 border border-lavender-border text-center shadow-xs">
              <div className="flex items-center justify-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-violet" />
                <span className="text-sm font-semibold text-ink">
                  Precedent Knowledge Search & Index
                </span>
              </div>
              <p className="text-xs text-ink-60 font-sans">
                Dense pgvector Embeddings + BM25 Lexical Keyword Index
              </p>
            </div>

            {/* Layer 3: Security & Governance */}
            <div className="p-3.5 rounded-2xl bg-canvas border border-sand-deep text-center">
              <div className="flex items-center justify-center gap-2 mb-0.5">
                <Lock className="w-3.5 h-3.5 text-ink-60" />
                <span className="text-xs font-semibold text-ink">
                  Security, Ethical Walls & Access Controls
                </span>
              </div>
              <p className="text-[11px] text-ink-40 font-mono">
                Clause-level permission filtering on every retrieval path
              </p>
            </div>

            {/* Layer 4: Data Sources Icons Grid */}
            <div className="pt-3 border-t border-sand-deep/60">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-40 block text-center mb-3">
                Data Sources & Integrations
              </span>
              <div className="flex items-center justify-center gap-3 sm:gap-4 text-ink-60 flex-wrap">
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <FileText className="w-3.5 h-3.5 text-violet" />
                  <span>SharePoint</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <Database className="w-3.5 h-3.5 text-violet" />
                  <span>iManage</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <Mail className="w-3.5 h-3.5 text-violet" />
                  <span>Outlook</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <MessageSquare className="w-3.5 h-3.5 text-violet" />
                  <span>Teams</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <HardDrive className="w-3.5 h-3.5 text-violet" />
                  <span>OneDrive</span>
                </div>
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-canvas text-xs font-mono">
                  <Globe className="w-3.5 h-3.5 text-violet" />
                  <span>SEC EDGAR</span>
                </div>
              </div>
            </div>
          </div>

          {/* Side Callout Annotations matching DeepJudge's side bullets */}
          <div className="flex flex-col gap-4 text-left">
            <div className="p-3.5 rounded-2xl bg-paper border border-sand-deep shadow-xs">
              <span className="text-xs font-semibold text-ink block mb-0.5">
                Transparent & Grounded
              </span>
              <span className="text-[11px] text-ink-60 leading-snug block">
                Deterministic LangGraph agent verifying citations before return.
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-paper border border-sand-deep shadow-xs">
              <span className="text-xs font-semibold text-ink block mb-0.5">
                Fast & Compliant
              </span>
              <span className="text-[11px] text-ink-60 leading-snug block">
                Sub-250ms hybrid retrieval across 13,000+ clauses.
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-paper border border-sand-deep shadow-xs">
              <span className="text-xs font-semibold text-ink block mb-0.5">
                Built-in Ethical Walls
              </span>
              <span className="text-[11px] text-ink-60 leading-snug block">
                Zero cross-tenant data leakage; access_group enforced in SQL.
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-paper border border-sand-deep shadow-xs">
              <span className="text-xs font-semibold text-ink block mb-0.5">
                Out-of-the-Box MCP
              </span>
              <span className="text-[11px] text-ink-60 leading-snug block">
                Exposes contract intelligence to Claude Desktop & CLI.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
