type SplitTag = "span" | "h1" | "h2" | "h3" | "p";

/**
 * Splits a headline into per-word spans so GSAP can stagger them.
 *
 * Renders as real words separated by non-breaking spaces, so the text stays
 * selectable, copyable, and readable by screen readers and crawlers - a
 * canvas- or aria-hidden-based split would break all three.
 *
 * The outer span clips each word so it can rise from below its own line box
 * without being cut off by the line above it.
 */
export function SplitText({
  text,
  className = "",
  as: Tag = "span",
}: {
  text: string;
  className?: string;
  as?: SplitTag;
}) {
  const words = text.split(" ");

  return (
    <Tag className={className}>
      {words.map((word, index) => (
        <span
          key={`${word}-${index}`}
          style={{
            display: "inline-block",
            overflow: "hidden",
            paddingBottom: "0.12em",
            marginBottom: "-0.12em",
            verticalAlign: "top",
          }}
        >
          <span
            data-split-word
            style={{ display: "inline-block", willChange: "transform" }}
          >
            {word}
            {index < words.length - 1 ? "\u00A0" : ""}
          </span>
        </span>
      ))}
    </Tag>
  );
}