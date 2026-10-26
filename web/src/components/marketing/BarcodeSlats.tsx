"use client";

import { useRef, useState } from "react";

interface BarcodeSlatsProps {
  className?: string;
  variant?: "hero" | "dense" | "lavender";
  interactive?: boolean;
}

/**
 * The signature DeepJudge barcode / slats generative waveform graphic.
 * Represents indexed document DNA, clause embeddings, and institutional knowledge.
 * Features rhythmic heights, diagonal accent slashes, vibrant violet lines, and interactive mouse ripple.
 */
export function BarcodeSlats({
  className = "",
  variant = "hero",
  interactive = true,
}: BarcodeSlatsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Generate 76 distinct slat heights and styles matching the screenshot pattern
  const slats = [
    { height: 55, type: "line" },
    { height: 35, type: "line" },
    { height: 75, type: "line" },
    { height: 95, type: "line" },
    { height: 40, type: "line" },
    { height: 80, type: "line" },
    { height: 60, type: "line" },
    { height: 100, type: "line" },
    { height: 45, type: "line" },
    { height: 70, type: "slash-right" },
    { height: 90, type: "line" },
    { height: 50, type: "line" },
    { height: 85, type: "line" },
    { height: 65, type: "line" },
    { height: 40, type: "line" },
    { height: 90, type: "violet" },
    { height: 95, type: "violet" },
    { height: 35, type: "line" },
    { height: 80, type: "line" },
    { height: 60, type: "line" },
    { height: 75, type: "slash-left" },
    { height: 45, type: "line" },
    { height: 85, type: "line" },
    { height: 90, type: "line" },
    { height: 30, type: "line" },
    { height: 70, type: "line" },
    { height: 55, type: "line" },
    { height: 100, type: "line" },
    { height: 40, type: "line" },
    { height: 85, type: "line" },
    { height: 60, type: "line" },
    { height: 95, type: "violet" },
    { height: 70, type: "line" },
    { height: 45, type: "slash-right" },
    { height: 80, type: "line" },
    { height: 35, type: "line" },
    { height: 90, type: "line" },
    { height: 60, type: "line" },
    { height: 75, type: "line" },
    { height: 40, type: "line" },
    { height: 85, type: "line" },
    { height: 100, type: "violet" },
    { height: 65, type: "line" },
    { height: 50, type: "line" },
    { height: 80, type: "line" },
    { height: 35, type: "slash-left" },
    { height: 70, type: "line" },
    { height: 90, type: "line" },
    { height: 45, type: "line" },
    { height: 60, type: "line" },
    { height: 85, type: "line" },
    { height: 40, type: "line" },
    { height: 95, type: "line" },
    { height: 70, type: "line" },
    { height: 55, type: "slash-right" },
    { height: 80, type: "line" },
    { height: 35, type: "line" },
    { height: 90, type: "line" },
    { height: 60, type: "line" },
    { height: 75, type: "violet" },
    { height: 100, type: "slash-right" },
    { height: 85, type: "line" },
    { height: 45, type: "line" },
    { height: 65, type: "line" },
    { height: 90, type: "line" },
    { height: 40, type: "line" },
    { height: 80, type: "line" },
    { height: 55, type: "line" },
    { height: 70, type: "line" },
    { height: 95, type: "line" },
    { height: 35, type: "line" },
    { height: 60, type: "line" },
    { height: 85, type: "slash-left" },
    { height: 50, type: "line" },
    { height: 75, type: "line" },
    { height: 90, type: "line" },
  ];

  return (
    <div
      ref={containerRef}
      className={`relative w-full select-none overflow-hidden ${className}`}
      onMouseLeave={() => setHoverIndex(null)}
    >
      <div className="flex items-center justify-between w-full h-32 md:h-44 px-2 sm:px-6">
        {slats.map((slat, index) => {
          // Calculate distance to hovered slat for organic magnetic ripple
          let scaleMultiplier = 1;
          if (hoverIndex !== null) {
            const distance = Math.abs(index - hoverIndex);
            if (distance < 6) {
              scaleMultiplier = 1 + (6 - distance) * 0.08;
            }
          }

          const isViolet = slat.type === "violet";
          const isSlashRight = slat.type === "slash-right";
          const isSlashLeft = slat.type === "slash-left";

          let lineColor = "bg-ink/80";
          if (variant === "lavender") {
            lineColor = isViolet ? "bg-violet" : "bg-violet/40";
          } else if (isViolet) {
            lineColor = "bg-violet shadow-[0_0_12px_rgba(124,58,237,0.7)]";
          }

          let transformStyle = "";
          if (isSlashRight) transformStyle = "rotate-[20deg] scale-y-110";
          if (isSlashLeft) transformStyle = "-rotate-[20deg] scale-y-110";

          return (
            <div
              key={index}
              className="relative flex items-center justify-center flex-1 h-full cursor-pointer group py-2"
              onMouseEnter={() => interactive && setHoverIndex(index)}
            >
              <div
                className={`w-[2px] sm:w-[2.5px] rounded-full transition-all duration-300 ease-out ${lineColor} ${transformStyle}`}
                style={{
                  height: `${Math.min(100, slat.height * scaleMultiplier)}%`,
                  opacity:
                    hoverIndex !== null && Math.abs(index - hoverIndex) < 5
                      ? 1
                      : isViolet
                        ? 1
                        : 0.65,
                }}
              />
              {/* Subtle top indicator for violet bars */}
              {isViolet && (
                <div
                  className="absolute w-1.5 h-1.5 rounded-full bg-violet animate-pulse pointer-events-none"
                  style={{
                    top: `${Math.max(8, 50 - slat.height / 2)}%`,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
