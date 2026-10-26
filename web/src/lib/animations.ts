"use client";

/**
 * GSAP animation layer for the marketing site.
 *
 * What this owns:
 *   - hero intro timeline (runs on mount, not on scroll)
 *   - split-text headline reveals (word-level, masked)
 *   - scroll-triggered section reveals and staggered groups
 *   - count-up statistics, infinite marquee, background parallax
 *   - scroll progress bar, nav hide/show, pipeline scrub, magnetic buttons
 *
 * What this does NOT own: anything inside the chat UI at /app. That surface
 * keeps plain CSS transitions so message rendering never waits on a timeline.
 *
 * Everything is created inside one gsap.context() and reverted on unmount, so
 * tweens and ScrollTriggers are cleaned up on fast-refresh too.
 *
 * Reduced motion: every effect is skipped and elements are landed in their
 * final state, so the page is fully readable with no animation at all.
 */
import { useLayoutEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

/** Register ScrollTrigger once, on the client only. */
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/** "Fast out, long settle" - the easing the whole site uses. */
const EASE = "power3.out";
const EASE_SOFT = "power2.inOut";

/** Stagger between words in a split headline. */
const WORD_STAGGER = 0.05;

/** How far below the viewport a reveal starts. */
const REVEAL_START = "top 88%";

export function useMarketingAnimations() {
  useLayoutEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const finePointer = window.matchMedia(
      "(hover: hover) and (pointer: fine)",
    ).matches;

    /**
     * Cleanup callbacks for anything the context callback creates that gsap
     * cannot tear down itself (DOM event listeners). Collected outside the
     * callback because `ctx` is still in its temporal dead zone while the
     * callback runs.
     */
    const cleanups: Array<() => void> = [];

    const ctx = gsap.context(() => {
      const splitWords = gsap.utils.toArray<HTMLElement>("[data-split-word]");

      /** Group split words by their nearest heading so each heading is one trigger. */
      const groupWords = (words: HTMLElement[]) => {
        const map = new Map<Element, HTMLElement[]>();
        words.forEach((word) => {
          const root = word.closest("h1, h2, h3, p, blockquote") ?? word;
          const existing = map.get(root);
          if (existing) existing.push(word);
          else map.set(root, [word]);
        });
        return map;
      };

      /* ---------------------------------------------------------------------
       * Reduced motion: land everything in its final state and stop here.
       * ------------------------------------------------------------------- */
      if (reduceMotion) {
        gsap.set("[data-reveal]", { opacity: 1, y: 0, clearProps: "transform" });
        gsap.set(splitWords, { opacity: 1, yPercent: 0, rotateX: 0 });
        gsap.set("[data-nav]", { yPercent: 0 });
        gsap.set("[data-progress]", { scaleX: 1 });
        return;
      }

      /* ---------------------------------------------------------------------
       * Hero intro. Runs on mount so the fold animates immediately instead of
       * waiting for a scroll trigger that is already satisfied at load.
       * ------------------------------------------------------------------- */
      const hero = document.querySelector<HTMLElement>("[data-hero-intro]");
      if (hero) {
        const heroWords = groupWords(
          Array.from(hero.querySelectorAll<HTMLElement>("[data-split-word]")),
        );
        const tl = gsap.timeline({ defaults: { ease: EASE } });

        heroWords.forEach((words) => {
          gsap.set(words, {
            opacity: 0,
            yPercent: 115,
            rotateX: -60,
            transformOrigin: "left bottom",
          });
          tl.to(
            words,
            {
              opacity: 1,
              yPercent: 0,
              rotateX: 0,
              duration: 1.15,
              stagger: WORD_STAGGER,
            },
            0.15,
          );
        });

        const heroReveals = hero.querySelectorAll<HTMLElement>("[data-reveal]");
        if (heroReveals.length) {
          gsap.set(heroReveals, { opacity: 0, y: 34, filter: "blur(6px)" });
          tl.to(
            heroReveals,
            {
              opacity: 1,
              y: 0,
              filter: "blur(0px)",
              duration: 1,
              stagger: 0.12,
            },
            0.1,
          );
        }

        // The scroll cue loops so it reads as an invitation rather than a marker.
        const cue = hero.querySelector<HTMLElement>("[data-scroll-cue]");
        if (cue) {
          gsap.fromTo(
            cue,
            { opacity: 0, y: -6 },
            { opacity: 1, y: 0, duration: 0.8, delay: 1.4, ease: EASE },
          );
          gsap.to(cue.querySelector("[data-cue-line]"), {
            scaleY: 0.25,
            transformOrigin: "top center",
            duration: 1.1,
            repeat: -1,
            yoyo: true,
            ease: EASE_SOFT,
            delay: 2,
          });
        }
      }

      /* ---------------------------------------------------------------------
       * Split-text reveals for every heading outside the hero.
       * ------------------------------------------------------------------- */
      const scrollWords = splitWords.filter((w) => !w.closest("[data-hero-intro]"));
      groupWords(scrollWords).forEach((words, target) => {
        if (words.length === 0) return;
        gsap.set(words, {
          opacity: 0,
          yPercent: 115,
          rotateX: -60,
          transformOrigin: "left bottom",
        });
        gsap.to(words, {
          opacity: 1,
          yPercent: 0,
          rotateX: 0,
          duration: 1.15,
          ease: EASE,
          stagger: WORD_STAGGER,
          scrollTrigger: { trigger: target, start: "top 85%", once: true },
        });
      });

      /* ---------------------------------------------------------------------
       * Section reveals. Standalone [data-reveal] fade+blur up individually,
       * groups stagger together.
       * ------------------------------------------------------------------- */
      const reveals = gsap.utils
        .toArray<HTMLElement>("[data-reveal]")
        .filter((el) => !el.closest("[data-hero-intro]"));

      reveals.forEach((el) => {
        gsap.fromTo(
          el,
          { opacity: 0, y: 30, filter: "blur(6px)" },
          {
            opacity: 1,
            y: 0,
            filter: "blur(0px)",
            duration: 0.95,
            ease: EASE,
            scrollTrigger: { trigger: el, start: REVEAL_START, once: true },
          },
        );
      });

      gsap.utils.toArray<HTMLElement>("[data-reveal-group]").forEach((group) => {
        const children = group.querySelectorAll("[data-reveal-item]");
        if (children.length === 0) return;
        gsap.fromTo(
          children,
          { opacity: 0, y: 42, filter: "blur(5px)" },
          {
            opacity: 1,
            y: 0,
            filter: "blur(0px)",
            duration: 0.9,
            ease: EASE,
            stagger: 0.11,
            scrollTrigger: { trigger: group, start: "top 82%", once: true },
          },
        );
      });

      /* ---------------------------------------------------------------------
       * Count-up statistics. The real number is rendered server-side so the
       * page reads correctly without JS; this animates from zero to it.
       * ------------------------------------------------------------------- */
      gsap.utils.toArray<HTMLElement>("[data-counter]").forEach((el) => {
        const to = parseFloat(el.dataset.counterTo ?? "0");
        const decimals = parseInt(el.dataset.counterDecimals ?? "0", 10);
        const counter = { value: 0 };
        gsap.fromTo(
          counter,
          { value: 0 },
          {
            value: to,
            duration: 2.2,
            ease: "power2.out",
            scrollTrigger: { trigger: el, start: "top 88%", once: true },
            onUpdate: () => {
              el.textContent = counter.value.toFixed(decimals);
            },
          },
        );
      });

      /* ---------------------------------------------------------------------
       * Marquee. Two copies of the row let a -50% translate loop seamlessly.
       * Scroll velocity nudges speed via timeScale, never reversing direction.
       * ------------------------------------------------------------------- */
      gsap.utils.toArray<HTMLElement>("[data-marquee]").forEach((track) => {
        const tween = gsap.to(track, {
          xPercent: -50,
          duration: 30,
          ease: "none",
          repeat: -1,
        });
        ScrollTrigger.create({
          trigger: track,
          start: "top bottom",
          end: "bottom top",
          onUpdate: (self) => {
            const boost = 1 + Math.abs(self.getVelocity() / 900);
            tween.timeScale(Math.min(boost, 5));
          },
        });
      });

      /* ---------------------------------------------------------------------
       * Parallax. Background washes drift relative to page scroll.
       * ------------------------------------------------------------------- */
      gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((layer) => {
        const strength = parseFloat(layer.dataset.parallax ?? "0.15");
        gsap.to(layer, {
          yPercent: strength * 100,
          ease: "none",
          scrollTrigger: {
            trigger: layer.parentElement ?? layer,
            start: "top top",
            end: "bottom top",
            scrub: 0.6,
          },
        });
      });

      /* ---------------------------------------------------------------------
       * Scroll progress bar: scaleX bound to whole-document scroll progress.
       * ------------------------------------------------------------------- */
      const progress = document.querySelector<HTMLElement>("[data-progress]");
      if (progress) {
        gsap.fromTo(
          progress,
          { scaleX: 0 },
          {
            scaleX: 1,
            ease: "none",
            scrollTrigger: {
              // Numeric start + "max" is the reliable way to span the whole
              // document; element-based start/end mis-measure on <html>.
              start: 0,
              end: "max",
              scrub: 0.3,
            },
          },
        );
      }

      /* ---------------------------------------------------------------------
       * Nav: hides while scrolling down, returns on scroll up.
       * Backdrop styling stays a CSS concern driven by [data-nav-scrolled].
       * ------------------------------------------------------------------- */
      const nav = document.querySelector<HTMLElement>("[data-nav]");
      if (nav) {
        let lastY = window.scrollY;
        ScrollTrigger.create({
          start: 0,
          end: "max",
          onUpdate: (self) => {
            const y = self.scroll();
            const goingDown = y > lastY;
            if (y < 120) {
              gsap.to(nav, { yPercent: 0, duration: 0.45, ease: EASE, overwrite: true });
            } else if (goingDown) {
              gsap.to(nav, { yPercent: -110, duration: 0.45, ease: EASE, overwrite: true });
            } else {
              gsap.to(nav, { yPercent: 0, duration: 0.45, ease: EASE, overwrite: true });
            }
            lastY = y;
          },
        });
      }

      /* ---------------------------------------------------------------------
       * Pipeline scrub. Rows in the architecture section pick up an active
       * state as each crosses the middle of the viewport, so the list reads
       * as a sequence rather than five static blocks.
       * ------------------------------------------------------------------- */
      const rows = gsap.utils.toArray<HTMLElement>("[data-pipeline-row]");
      rows.forEach((row) => {
        ScrollTrigger.create({
          trigger: row,
          start: "top 65%",
          end: "bottom 45%",
          onToggle: (self) => row.classList.toggle("is-active", self.isActive),
        });
      });

      /* ---------------------------------------------------------------------
       * Magnetic buttons. Fine pointers only - touch devices get no follow.
       * ------------------------------------------------------------------- */
      if (finePointer) {
        gsap.utils.toArray<HTMLElement>("[data-magnetic]").forEach((el) => {
          const strength = parseFloat(el.dataset.magnetic ?? "0.35");
          const moveX = gsap.quickTo(el, "x", { duration: 0.5, ease: EASE });
          const moveY = gsap.quickTo(el, "y", { duration: 0.5, ease: EASE });

          const onMove = (e: PointerEvent) => {
            const r = el.getBoundingClientRect();
            moveX((e.clientX - (r.left + r.width / 2)) * strength);
            moveY((e.clientY - (r.top + r.height / 2)) * strength);
          };
          const onLeave = () => {
            moveX(0);
            moveY(0);
          };

          el.addEventListener("pointermove", onMove);
          el.addEventListener("pointerleave", onLeave);
          cleanups.push(() => {
            el.removeEventListener("pointermove", onMove);
            el.removeEventListener("pointerleave", onLeave);
          });
        });
      }

      /* ---------------------------------------------------------------------
       * Closing CTA: slow breathing scale so the page resolves on a live element.
       * ------------------------------------------------------------------- */
      const closingCta = document.querySelector<HTMLElement>("[data-cta-pulse]");
      if (closingCta) {
        gsap.to(closingCta, {
          scale: 1.015,
          duration: 3,
          ease: "sine.inOut",
          repeat: -1,
          yoyo: true,
          transformOrigin: "center center",
        });
      }
    });

    // Web fonts change metrics after load, so trigger positions need refreshing.
    const refresh = () => ScrollTrigger.refresh();
    document.fonts?.ready.then(refresh).catch(() => undefined);
    window.addEventListener("load", refresh);
    const refreshTimer = window.setTimeout(refresh, 800);

    return () => {
      window.removeEventListener("load", refresh);
      window.clearTimeout(refreshTimer);
      // Listener cleanups first, then revert tweens/ScrollTriggers.
      cleanups.forEach((fn) => fn());
      ctx.revert();
    };
  }, []);
}
