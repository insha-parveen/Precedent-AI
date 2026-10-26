"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X, ArrowRight } from "lucide-react";

const NAV_LINKS = [
  { label: "Product", href: "#workflows" },
  { label: "Platform", href: "#platform" },
  { label: "Knowledge Graph", href: "#knowledge" },
  { label: "Evaluation", href: "#stats" },
  { label: "Insights", href: "#insights" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (menuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <header
      data-nav
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-canvas/90 backdrop-blur-md border-b border-sand py-3"
          : "bg-transparent border-b border-transparent py-5"
      }`}
    >
      <nav className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* Logo & Mark */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="w-8 h-8 rounded-full bg-ink flex items-center justify-center text-canvas font-serif font-bold text-sm transition-transform duration-300 group-hover:scale-105">
            P
          </div>
          <span className="text-lg font-serif font-normal tracking-tight text-ink">
            Precedent
          </span>
        </Link>

        {/* Center Nav Links */}
        <ul className="hidden lg:flex items-center gap-8">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                className="text-xs font-sans text-ink-60 hover:text-ink transition-colors duration-300 link-underline font-medium tracking-wide"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <a
            href="#platform"
            className="hidden sm:inline-flex items-center text-xs font-medium text-ink-60 hover:text-ink px-3 py-2 transition-colors"
          >
            Book Demo
          </a>

          <Link
            href="/app"
            className="inline-flex items-center gap-1.5 rounded-full bg-ink px-5 py-2.5 text-xs font-medium text-canvas transition-all duration-300 hover:bg-violet hover:scale-[1.02] shadow-xs"
          >
            <span>Open Agent</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="lg:hidden p-2 -mr-2 text-ink"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile sheet */}
      <div
        className={`lg:hidden overflow-hidden bg-canvas transition-[max-height,opacity] duration-500 ${
          menuOpen ? "max-h-96 opacity-100 border-t border-sand" : "max-h-0 opacity-0"
        }`}
      >
        <ul className="px-6 py-4 flex flex-col gap-1">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="block py-2.5 text-sm text-ink-60 hover:text-ink transition-colors"
              >
                {link.label}
              </a>
            </li>
          ))}
          <li className="pt-3 sm:hidden">
            <Link
              href="/app"
              onClick={() => setMenuOpen(false)}
              className="block rounded-full bg-ink px-5 py-3 text-center text-xs font-medium text-canvas"
            >
              Open Agent
            </Link>
          </li>
        </ul>
      </div>
    </header>
  );
}
