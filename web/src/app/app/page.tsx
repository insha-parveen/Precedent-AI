import { ChatContainer } from "@/components/ChatContainer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Precedent - Ask the agent",
  description: "Query the retrieval-first contract-intelligence agent",
};

/**
 * The interactive chat surface.
 *
 * Deliberately outside the marketing page's GSAP layer: message rendering,
 * the document drawer, and the loading indicator all use plain CSS transitions
 * so the UI stays correct with JavaScript animation disabled.
 */
export default function AppPage() {
  return (
    <div className="flex flex-col min-h-screen bg-canvas">
      <ChatContainer />
    </div>
  );
}
