"use client";

import { useChat } from "@/hooks/useChat";
import { Loader2, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { DocumentDrawer } from "./DocumentDrawer";
import { MessageBubble } from "./MessageBubble";

export function ChatContainer() {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    fetchDocument,
    closeDrawer,
    selectedDocId,
    documentData,
    isDrawerOpen,
  } = useChat();

  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const query = inputValue.trim();
    setInputValue("");
    await sendMessage(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl w-full mx-auto px-4 py-6">
      {/* Header */}
      <header className="mb-8 text-center">
        <h1 className="font-serif text-3xl font-bold text-ink mb-2">
          Precedent
        </h1>
        <p className="text-ink-60 text-lg">Contract Intelligence Agent</p>
        <p className="text-ink-60 text-sm mt-1">
          Retrieval-first Â· Citation-backed Â· Verified
        </p>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-2 pb-8">
        {messages.length === 0 && !isLoading && (
          <div className="text-center text-ink-40 py-12">
            <p className="text-lg mb-2">Ask a question about contracts</p>
            <p className="text-sm">
              e.g., "Find governing law clauses in merger agreements"
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            isUser={false}
            onCitationClick={fetchDocument}
          />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start mb-6">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-ink/10 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-ink animate-spin" />
              </div>
              <div className="bg-white border border-sand-deep rounded-2xl px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <span
                    className="w-2 h-2 bg-ink rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-2 h-2 bg-ink rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="w-2 h-2 bg-ink rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about contracts..."
            disabled={isLoading}
            rows={1}
            className={`
              w-full min-h-[56px] max-h-48 px-4 py-3 pr-14
              bg-white border border-sand-deep rounded-xl
              text-ink placeholder-neutral-400
              focus:border-ink focus:ring-2 focus:ring-ink/20
              disabled:bg-sand disabled:cursor-not-allowed
              resize-none transition-colors
              font-sans text-base leading-relaxed
            `}
            aria-label="Your question"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className={`
              absolute right-2 bottom-2 p-2 rounded-lg transition-colors
              ${
                !inputValue.trim() || isLoading
                  ? "text-ink-40 cursor-not-allowed"
                  : "text-ink hover:bg-ink/10"
              }
            `}
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-ink-40 text-center mt-2">
          Press Enter to send Â· Shift+Enter for new line
        </p>
      </form>

      {/* Document Drawer */}
      <DocumentDrawer
        document={documentData}
        isOpen={isDrawerOpen}
        onClose={closeDrawer}
      />
    </div>
  );
}
