"use client";
import { useState, useCallback } from "react";
import { api, streamChat } from "@/lib/api";
import type { Message, Conversation } from "@/types";

export function useChat() {
  const [messages, setMessages]           = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId]   = useState<string | null>(() => {
    if (typeof window === "undefined") return null;   // server → no localStorage
    return localStorage.getItem("active_conv_id");    // browser → restore last conv
  });
  const [loading, setLoading]   = useState(false);
  const [streaming, setStreaming] = useState(false);

  // ── Save active conv id to localStorage so it survives page refresh ────
  const updateActiveConvId = useCallback((id: string | null) => {
    setActiveConvId(id);
    if (typeof window !== "undefined") {
      if (id) localStorage.setItem("active_conv_id", id);
      else    localStorage.removeItem("active_conv_id");
    }
  }, []);

  // ── Load conversation list ──────────────────────────────────────────────
  const loadConversations = useCallback(async () => {
    try {
      const list = await api.get<Conversation[]>("/api/conversations");
      if (Array.isArray(list)) setConversations(list);
    } catch {}
  }, []);

  // ── Load single conversation with messages ──────────────────────────────
  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await api.get<Conversation>(`/api/conversations/${id}`);
      if (conv && typeof conv === "object" && !Array.isArray(conv)) {
        setMessages((conv.messages as Message[]) || []);
        updateActiveConvId(id);
      }
    } catch {}
  }, [updateActiveConvId]);

  // ── Send message + stream response ─────────────────────────────────────
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };
    setMessages(prev => [...prev, userMsg]);
    setStreaming(true);

    const aiMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: aiMsgId, role: "assistant", content: "" }]);

    await streamChat(
      text,
      activeConvId,
      // onChunk
      (chunk) => setMessages(prev =>
        prev.map(m => m.id === aiMsgId ? { ...m, content: m.content + chunk } : m)
      ),
      // onConvId
      (convId) => {
        updateActiveConvId(convId);
        loadConversations();
      },
      // onDone
      () => setStreaming(false),
      // onError
      (err) => {
        setMessages(prev =>
          prev.map(m => m.id === aiMsgId
            ? { ...m, content: `Sorry, something went wrong: ${err}` }
            : m
          )
        );
        setStreaming(false);
      }
    );
  }, [activeConvId, streaming, loadConversations, updateActiveConvId]);

  // ── Start a new conversation ────────────────────────────────────────────
  const newConversation = useCallback(() => {
    setMessages([]);
    updateActiveConvId(null);  // clears localStorage too
  }, [updateActiveConvId]);

  // ── Delete a conversation ───────────────────────────────────────────────
  const deleteConversation = useCallback(async (id: string) => {
    try {
      await api.delete(`/api/conversations/${id}`);
    } catch {}
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConvId === id) newConversation();
  }, [activeConvId, newConversation]);

  const renameConversation = useCallback(async (id: string, title: string) => {
    const trimmedTitle = title.trim();
    if (!trimmedTitle) throw new Error("Conversation title cannot be empty");

    const updated = await api.patch<Conversation>(`/api/conversations/${id}`, {
      title: trimmedTitle,
    });

    setConversations(prev =>
      prev.map(c => (c.id === id ? { ...c, title: updated.title, updated_at: updated.updated_at } : c))
    );
  }, []);

  return {
    messages,
    conversations,
    activeConvId,
    loading,
    streaming,
    loadConversations,
    loadConversation,
    sendMessage,
    newConversation,
    deleteConversation,
    renameConversation,
  };
}
