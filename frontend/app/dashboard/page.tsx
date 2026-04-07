"use client";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { ArrowDown } from "lucide-react";
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
    loadConversations, loadConversation, sendMessage, newConversation, deleteConversation, renameConversation,
  } = useChat();
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const convLoadedRef = useRef(false);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

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

  function focusInput() {
    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  }

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;
      setShowScrollToBottom(distanceFromBottom > 120);
    };

    handleScroll();
    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [messages.length, activeConvId]);

  async function handleSend() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    focusInput();
    await sendMessage(text);
    focusInput();
  }

  function handleScrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
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
          onRename={renameConversation}
        />

        {/* Main chat area */}
        <main className="relative flex-1 flex flex-col overflow-hidden">
          <div ref={scrollContainerRef} className="flex-1 overflow-y-auto flex" >
            <div className="flex-1 flex flex-col max-w-3xl mx-auto px-4 pt-24 pb-6 w-full">
              {messages.length === 0 ? (
                <WelcomeScreen name={user.full_name} onSuggest={text => { setInput(text); }} />
              ) : (
                <>
                  {messages.map(msg => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {streaming && messages[messages.length - 1]?.role === "user" && <TypingIndicator />}
                  <div ref={bottomRef} className="h-8 shrink-0" />
                </>
              )}
            </div>
          </div>

          {showScrollToBottom && (
            <button
              onClick={handleScrollToBottom}
              className="absolute bottom-28 left-1/2 z-20 flex h-11 w-11 -translate-x-1/2 items-center justify-center rounded-full border border-red-200 bg-white text-red-600 shadow-lg transition-all hover:bg-red-30"
              aria-label="Scroll to bottom"
            >
              <ArrowDown size={20} />
            </button>
          )}

          <InputBar
            ref={inputRef}
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
