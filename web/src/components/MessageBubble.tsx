"use client";

import { ChatResponse } from "@/types/api";
import { Bot, Send, User } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { SkillIndicator } from "./SkillIndicator";

interface MessageBubbleProps {
  message: ChatResponse;
  isUser: boolean;
  onCitationClick: (docId: number) => void;
}

export function MessageBubble({
  message,
  isUser,
  onCitationClick,
}: MessageBubbleProps) {
  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex max-w-[80%] flex-col items-end">
          <div className="relative rounded-2xl bg-ink px-4 py-3 text-white shadow-sm">
            <p className="text-canvas leading-relaxed">{message.answer}</p>
          </div>
          <div className="flex items-center gap-1 mt-1 text-xs text-ink-40">
            <User className="w-3 h-3" />
            <span>You</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="flex max-w-[85%] flex-col items-start">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-ink/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-ink" />
          </div>
          <div className="flex-1 min-w-0">
            <SkillIndicator
              skill={message.skill_used}
              grounded={message.grounded}
            />
            <div className="relative rounded-2xl bg-white border border-sand-deep px-4 py-3 shadow-sm">
              <MarkdownRenderer
                content={message.answer}
                onCitationClick={onCitationClick}
              />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 mt-1 text-xs text-ink-40 ml-11">
          <Send className="w-3 h-3" />
          <span>Precedent</span>
          {message.latency_ms && (
            <>
              <span>Â·</span>
              <span>{message.latency_ms}ms</span>
            </>
          )}
          {message.input_tokens && message.output_tokens && (
            <>
              <span>Â·</span>
              <span>{message.input_tokens + message.output_tokens} tokens</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
