"use client";
import { useState, useCallback } from "react";
import { api, streamChat } from "@/lib/api";
import type { Message, Conversation } from "@/types";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      const list = await api.get<Conversation[]>("/api/conversations");
      setConversations(list);
    } catch {}
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await api.get<Conversation>(`/api/conversations/${id}`);
      setMessages(conv.messages || []);
      setActiveConvId(id);
    } catch {}
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setStreaming(true);

    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: Message = { id: aiMsgId, role: "assistant", content: "" };
    setMessages(prev => [...prev, aiMsg]);

    await streamChat(
      text,
      activeConvId,
      (chunk) => setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: m.content + chunk } : m)),
      (convId) => {
        setActiveConvId(convId);
        loadConversations();
      },
      () => setStreaming(false),
      (err) => {
        setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: `Sorry, something went wrong: ${err}` } : m));
        setStreaming(false);
      }
    );
  }, [activeConvId, streaming, loadConversations]);

  const newConversation = useCallback(() => {
    setMessages([]);
    setActiveConvId(null);
  }, []);

  const deleteConversation = useCallback(async (id: string) => {
    await api.delete(`/api/conversations/${id}`);
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConvId === id) newConversation();
  }, [activeConvId, newConversation]);

  return {
    messages, conversations, activeConvId, loading, streaming,
    loadConversations, loadConversation, sendMessage, newConversation, deleteConversation,
  };
}
