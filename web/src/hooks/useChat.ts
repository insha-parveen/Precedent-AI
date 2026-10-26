"use client";

import { useState, useCallback } from "react";
import { ChatRequest, ChatResponse, DocumentResponse } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export function useChat() {
  const [messages, setMessages] = useState<ChatResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [documentData, setDocumentData] = useState<DocumentResponse | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const sendMessage = useCallback(async (query: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query } as ChatRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMessages((prev) => [...prev, data]);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send message";
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchDocument = useCallback(async (docId: number) => {
    try {
      const response = await fetch(`${API_BASE}/api/document/${docId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDocumentData(data);
      setSelectedDocId(docId);
      setIsDrawerOpen(true);
    } catch (err) {
      console.error("Failed to fetch document:", err);
    }
  }, []);

  const closeDrawer = useCallback(() => {
    setIsDrawerOpen(false);
    setDocumentData(null);
    setSelectedDocId(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    fetchDocument,
    closeDrawer,
    selectedDocId,
    documentData,
    isDrawerOpen,
  };
}