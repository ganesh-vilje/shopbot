"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/chat/Sidebar";
import MessageBubble from "@/components/chat/MessageBubble";
import TypingIndicator from "@/components/chat/TypingIndicator";
import WelcomeScreen from "@/components/chat/WelcomeScreen";
import InputBar from "@/components/chat/InputBar";
import { useAuth } from "@/hooks/useAuth";
import { useChat } from "@/hooks/useChat";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading, logout } = useAuth();
  const {
    messages, conversations, activeConvId, streaming,
    loadConversations, loadConversation, sendMessage, newConversation, deleteConversation,
  } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const convLoadedRef = useRef(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

useEffect(() => {
  if (user && !convLoadedRef.current) {
    convLoadedRef.current = true;
    loadConversations().then(() => {
      // After conversations load, restore the last active one
      const savedConvId = localStorage.getItem("active_conv_id");
      if (savedConvId) {
        loadConversation(savedConvId);
      }
    });
  }
}, [user, loadConversations, loadConversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  async function handleSend() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    await sendMessage(text);
  }

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-t-transparent animate-spin" style={{borderColor:"#C0392B", borderTopColor:"transparent"}} />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      <Navbar user={user} onLogout={logout} />

      <div className="flex flex-1 overflow-hidden" style={{paddingTop:"6px"}}>
        <Sidebar
          conversations={conversations}
          activeId={activeConvId}
          onSelect={loadConversation}
          onNew={newConversation}
          onDelete={deleteConversation}
        />

        {/* Main chat area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto flex" >
            <div className="flex-1 flex flex-col max-w-3xl mx-auto px-4 pt-24 pb-50 w-full">
              {messages.length === 0 ? (
                <WelcomeScreen name={user.full_name} onSuggest={text => { setInput(text); }} />
              ) : (
                <>
                  {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {streaming && messages[messages.length - 1]?.role === "user" && <TypingIndicator />}
                  <div ref={bottomRef} />
                </>
              )}
            </div>
          </div>

          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={handleSend}
            disabled={streaming}
          />
        </main>
      </div>
    </div>
  );
}
