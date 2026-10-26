# UI direction

## Decision

**Superseded 2026-10-05 by ADR-015.** The previous decision here was to avoid
replicating deepjudge.ai's visual design, animations, or brand identity. That
decision was reversed on an explicit instruction from the project owner, who
asked for the marketing site to follow deepjudge.ai's typography treatment and
scroll-animation approach as closely as the technology allows, while keeping
Precedent's own name, copy, product claims, and data.

The current rule is: **match the craft, never the identity.**

## What "match the craft" means in practice

Taken from deepjudge.ai, deliberately reimplemented:

- **The warm neutral palette.** A warm near-black ink (`#242422`) on a warm
  off-white canvas (`#f2f0ed`), with a sand tone (`#e4ded8`) for borders and
  raised surfaces. Defined once as tokens in `web/src/app/globals.css` and
  exposed to Tailwind in `web/tailwind.config.ts`.
- **The type roles.** A neutral grotesque for display/UI, a monospace for
  labels, eyebrows, citation IDs, and metadata, and a serif reserved for
  long-form legal text in the chat UI.
- **The motion language.** GSAP + ScrollTrigger: split-text headline reveals
  with a per-word stagger, staggered section reveals on scroll entry, count-up
  statistics, an infinite marquee, and subtle background parallax. This is the
  same technique set, implemented in `web/src/lib/animations.ts`.
- **The page rhythm.** Hero, capability grid, dark architecture band,
  sticky-column feature list, statistics band, marquee, closing CTA, mega-footer.

## What is never copied, and why

These are the parts that make the result Precedent rather than a reproduction:

- **Brand assets.** No logo, wordmark, illustration, photograph, icon set,
  customer logo, or Lottie animation from deepjudge.ai. All iconography is
  `lucide-react`.
- **Copy.** All headlines, body text, and CTAs are written for Precedent. No
  sentences lifted from their site, and no fabricated client testimonials,
  partner names, or firm logos to imitate their social-proof sections.
- **Statistics.** Every number on the page comes from this repository's own
  data (corpus sizes) or its own eval run (`recall@10`). Their "+65h saved per
  user per year" and similar figures are **not** ours and are not used. If the
  eval number changes, the page changes with it.
- **Fonts.** deepjudge.ai sets Suisse Intl, a commercially licensed family we
  do not have a license for. We substitute open equivalents with a similar
  role and metrics: **Archivo** (display/UI), **IBM Plex Mono** (labels and
  metadata), **Merriweather** (long-form serif in the chat UI).
- **Runtime.** We do not load Webflow's `webflow.js` or the rest of their
  script bundle. Webflow's runtime is proprietary, is coupled to their generated
  markup, and does not belong in a Next.js app. The equivalent effects are
  written directly against GSAP.

## Interaction patterns that are not negotiable

Carried over from the previous version of this document, because these express
the product's guarantees rather than its styling:

- **Chat-first, not dashboard-first.** One question box is the primary
  affordance, matching how the harness actually works.
- **Citations as inline, clickable chips.** `[doc:ID]` maps to a UI element
  that opens the source clause. Making the citation checkable is the whole
  point of ADR-005.
- **A visible "skill used" indicator** on each answer, so the routing decision
  is surfaced rather than hidden.
- **Motion is never load-bearing.** Every animation is decorative. Under
  `prefers-reduced-motion: reduce` the page renders in its final state with no
  reveals, counters, or marquee, and the chat UI never depends on an animation
  timeline to function.

## Where the motion lives

- `web/src/lib/animations.ts` — the entire GSAP layer, registered in one
  `gsap.context()` and reverted on unmount.
- `web/src/components/marketing/` — landing page sections, all `"use client"`.
- `web/src/app/page.tsx` — marketing landing page.
- `web/src/app/app/page.tsx` — the interactive chat UI, deliberately outside
  the GSAP layer so message rendering never waits on a timeline.

## When to revisit

If the marketing page starts making claims the backend cannot back, fix the
page. The eval numbers, the corpus sizes, and the skill list are all read from
the repository and must never drift from reality.
