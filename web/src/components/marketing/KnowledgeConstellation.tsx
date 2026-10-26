"use client";

import { useState } from "react";
import { SplitText } from "./SplitText";
import { Database, FileText, Mail, MessageSquare, HardDrive, Layers, Globe } from "lucide-react";

interface NodeItem {
  id: string;
  label: string;
  type: "card" | "pill";
  icon: typeof FileText;
  x: number;
  y: number;
  meta?: string;
}

const NODES: NodeItem[] = [
  { id: "sharepoint", label: "SHAREPOINT", type: "card", icon: FileText, x: 0, y: -42, meta: "3,400+ Files" },
  { id: "experience", label: "EXPERIENCE MANAGEMENT", type: "pill", icon: Layers, x: -38, y: -30 },
  { id: "dms", label: "DMS / iMANAGE", type: "card", icon: Database, x: -40, y: 10, meta: "Matter Workspaces" },
  { id: "email", label: "EMAIL & OUTLOOK", type: "pill", icon: Mail, x: -24, y: 38 },
  { id: "intranet", label: "INTRANET", type: "card", icon: Globe, x: 38, y: 22, meta: "Firm Knowledge" },
  { id: "onedrive", label: "ONEDRIVE", type: "card", icon: HardDrive, x: 36, y: -18, meta: "Drafts & Briefs" },
  { id: "teams", label: "TEAMS & CHANNELS", type: "pill", icon: MessageSquare, x: 32, y: -40 },
];

/**
 * Section 3 from DeepJudge:
 * "Your collective knowledge is your unique asset / But it's scattered and inaccessible"
 * Radial constellation of data silos connecting back to the institutional hub.
 */
export function KnowledgeConstellation() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  return (
    <section className="py-28 md:py-40 bg-canvas relative overflow-hidden">
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
      `}</style>
      <div className="max-w-7xl mx-auto px-6">
        {/* Constellation Canvas Container */}
        <div className="relative min-h-[580px] md:min-h-[680px] flex flex-col items-center justify-center">
          {/* Background Connecting SVG Web */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
            viewBox="0 0 1000 680"
            fill="none"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Center origin coordinate at (500, 340) */}
            <circle cx="500" cy="340" r="160" stroke="#ded7f5" strokeWidth="1" strokeDasharray="4 6" opacity="0.6" />
            <circle cx="500" cy="340" r="280" stroke="#e6e1d9" strokeWidth="1" strokeDasharray="3 8" opacity="0.5" />

            {/* Connecting lines to each node */}
            <path
              d="M 500 340 L 500 130"
              stroke={activeNode === "sharepoint" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "sharepoint" ? "2" : "1"}
              strokeDasharray={activeNode === "sharepoint" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 220 180"
              stroke={activeNode === "experience" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "experience" ? "2" : "1"}
              strokeDasharray={activeNode === "experience" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 200 390"
              stroke={activeNode === "dms" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "dms" ? "2" : "1"}
              strokeDasharray={activeNode === "dms" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 320 540"
              stroke={activeNode === "email" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "email" ? "2" : "1"}
              strokeDasharray={activeNode === "email" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 790 440"
              stroke={activeNode === "intranet" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "intranet" ? "2" : "1"}
              strokeDasharray={activeNode === "intranet" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 770 240"
              stroke={activeNode === "onedrive" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "onedrive" ? "2" : "1"}
              strokeDasharray={activeNode === "onedrive" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
            <path
              d="M 500 340 L 750 120"
              stroke={activeNode === "teams" ? "#7c3aed" : "#d8d1c7"}
              strokeWidth={activeNode === "teams" ? "2" : "1"}
              strokeDasharray={activeNode === "teams" ? "none" : "3 3"}
              className="transition-all duration-300"
            />
          </svg>

          {/* Central Typography Hub */}
          <div className="relative z-10 max-w-xl text-center px-6 py-12 rounded-3xl bg-canvas/70 backdrop-blur-xs">
            <SplitText
              as="h2"
              text="Your collective knowledge is your unique asset"
              className="text-[clamp(2.15rem,4vw,3.25rem)] font-serif font-normal leading-[1.08] tracking-[-0.03em] text-ink block mb-4"
            />
            <p data-reveal className="text-base md:text-lg text-ink-60 font-sans leading-relaxed">
              But it&apos;s scattered and inaccessible
            </p>
          </div>

          {/* Floating Silo Nodes - Visible on desktop / tablet */}
          <div className="hidden md:block absolute inset-0 pointer-events-none">
            {/* Top Node: SHAREPOINT */}
            <div
              className="absolute top-[8%] left-1/2 -translate-x-1/2 pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '0s' }}
              onMouseEnter={() => setActiveNode("sharepoint")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className={`flex flex-col items-center bg-paper rounded-xl border p-3 shadow-sm transition-all duration-300 ${activeNode === 'sharepoint' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light hover:shadow-md'}`}>
                <div className="flex items-center gap-2 mb-1.5">
                  <FileText className="w-3 h-3 text-ink-40" />
                  <span className="text-[10px] font-mono tracking-wider text-ink-60 uppercase">
                    SHAREPOINT
                  </span>
                </div>
                <div className="flex items-center gap-[2px] h-6 w-20 px-1 bg-canvas rounded">
                  {Array.from({ length: 14 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-ink/70 rounded-full"
                      style={{ height: `${25 + (i * 17) % 75}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Top-Left: EXPERIENCE MANAGEMENT */}
            <div
              className="absolute top-[16%] left-[12%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '0.2s' }}
              onMouseEnter={() => setActiveNode("experience")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <span className={`inline-flex items-center gap-2 rounded-full bg-paper px-4 py-1.5 text-[11px] font-mono tracking-wider text-ink-60 border shadow-xs transition-all duration-300 ${activeNode === 'experience' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light'}`}>
                <Layers className="w-3 h-3 text-ink-40" />
                EXPERIENCE MANAGEMENT
              </span>
            </div>

            {/* Left: DMS */}
            <div
              className="absolute top-[52%] left-[8%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '0.4s' }}
              onMouseEnter={() => setActiveNode("dms")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className={`flex flex-col bg-paper rounded-xl border p-3.5 shadow-sm transition-all duration-300 ${activeNode === 'dms' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light hover:shadow-md'} w-32`}>
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-3 h-3 text-ink-40" />
                  <span className="text-[10px] font-mono tracking-wider text-ink-60 uppercase">
                    DMS
                  </span>
                </div>
                <div className="flex items-center gap-[2px] h-5 w-full bg-canvas rounded px-1">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-ink/60 rounded-full"
                      style={{ height: `${30 + (i * 19) % 70}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom-Left: EMAIL */}
            <div
              className="absolute bottom-[10%] left-[24%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '0.6s' }}
              onMouseEnter={() => setActiveNode("email")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <span className={`inline-flex items-center gap-2 rounded-full bg-paper px-4 py-1.5 text-[11px] font-mono tracking-wider text-ink-60 border shadow-xs transition-all duration-300 ${activeNode === 'email' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light'}`}>
                <Mail className="w-3 h-3 text-ink-40" />
                EMAIL
              </span>
            </div>

            {/* Top-Right: TEAMS */}
            <div
              className="absolute top-[12%] right-[16%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '0.8s' }}
              onMouseEnter={() => setActiveNode("teams")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <span className={`inline-flex items-center gap-2 rounded-full bg-paper px-4 py-1.5 text-[11px] font-mono tracking-wider text-ink-60 border shadow-xs transition-all duration-300 ${activeNode === 'teams' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light'}`}>
                <MessageSquare className="w-3 h-3 text-ink-40" />
                TEAMS
              </span>
            </div>

            {/* Right: ONEDRIVE */}
            <div
              className="absolute top-[32%] right-[10%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '1s' }}
              onMouseEnter={() => setActiveNode("onedrive")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className={`flex flex-col bg-paper rounded-xl border p-3.5 shadow-sm transition-all duration-300 ${activeNode === 'onedrive' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light hover:shadow-md'} w-32`}>
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="w-3 h-3 text-ink-40" />
                  <span className="text-[10px] font-mono tracking-wider text-ink-60 uppercase">
                    ONEDRIVE
                  </span>
                </div>
                <div className="flex items-center gap-[2px] h-5 w-full bg-canvas rounded px-1">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-ink/60 rounded-full"
                      style={{ height: `${20 + (i * 23) % 80}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom-Right: INTRANET */}
            <div
              className="absolute bottom-[16%] right-[12%] pointer-events-auto cursor-pointer transition-all duration-500 hover:scale-110 animate-float"
              style={{ animationDelay: '1.2s' }}
              onMouseEnter={() => setActiveNode("intranet")}
              onMouseLeave={() => setActiveNode(null)}
            >
              <div className={`flex flex-col bg-paper rounded-xl border p-3 shadow-sm transition-all duration-300 ${activeNode === 'intranet' ? 'border-violet-500 shadow-violet-200 ring-2 ring-violet-500/20' : 'border-sand-deep hover:border-violet-light hover:shadow-md'} w-28`}>
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-3 h-3 text-ink-40" />
                  <span className="text-[10px] font-mono tracking-wider text-ink-60 uppercase">
                    INTRANET
                  </span>
                </div>
                <div className="flex items-center gap-[2px] h-5 w-full bg-canvas rounded px-1">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-ink/60 rounded-full"
                      style={{ height: `${35 + (i * 13) % 65}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Explanatory Paragraph */}
        <div data-reveal className="max-w-2xl mx-auto text-center mt-12 md:mt-16">
          <p className="text-sm md:text-base text-ink-60 font-sans leading-relaxed">
            Knowledge search indexes and understands your data, wherever it lives, providing
            seamless access to your knowledge from a single place. No complex implementation,
            no data migration: just instant, intelligent search.
          </p>
        </div>
      </div>
    </section>
  );
}
