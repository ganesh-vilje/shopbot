"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, ShoppingBag } from "lucide-react";
import type { Message } from "@/types";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const showAssistantLoading = !isUser && !message.content.trim();
  const timestamp = formatMessageTime(message.created_at);
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!message.content.trim()) return;

    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div
      className={`message-enter flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      {!isUser && (
        <div
          className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
          style={{ background: "#C0392B" }}
        >
          <ShoppingBag size={16} color="white" />
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`w-full text-sm leading-relaxed ${
            isUser
              ? "min-w-[64px] rounded-2xl rounded-tr-sm px-4 py-3 text-white"
              : showAssistantLoading
                ? "px-1 py-2 text-gray-800"
                : "rounded-2xl rounded-tl-sm px-4 py-3 text-gray-800"
          }`}
          style={
            isUser
              ? { background: "#C0392B" }
              : showAssistantLoading
                ? {}
                : { background: "#F9EBEA", border: "1px solid #F5C6C3" }
          }
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : showAssistantLoading ? (
            <>
              <div className="flex items-center gap-1.5 h-5">
                <span
                  className="message-loading-dot"
                  style={{ animationDelay: "0s" }}
                />
                <span
                  className="message-loading-dot"
                  style={{ animationDelay: "0.18s" }}
                />
                <span
                  className="message-loading-dot"
                  style={{ animationDelay: "0.36s" }}
                />
              </div>
              <style jsx>{`
                .message-loading-dot {
                  width: 8px;
                  height: 8px;
                  border-radius: 9999px;
                  background: #f35212;
                  display: inline-block;
                  animation: messageLoadingBounce 1.1s ease-in-out infinite;
                }

                @keyframes messageLoadingBounce {
                  0%,
                  100% {
                    transform: translateY(0);
                    opacity: 0.45;
                  }
                  50% {
                    transform: translateY(-5px);
                    opacity: 1;
                  }
                }
              `}</style>
            </>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => (
                  <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>
                ),
                li: ({ children }) => <li>{children}</li>,
                strong: ({ children }) => (
                  <strong className="font-semibold" style={{ color: "#922B21" }}>
                    {children}
                  </strong>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    className="underline"
                    style={{ color: "#C0392B" }}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {children}
                  </a>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="text-xs border-collapse w-full">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th
                    className="px-2 py-1 text-left font-semibold border"
                    style={{ background: "#F9EBEA", borderColor: "#F5C6C3" }}
                  >
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td
                    className="px-2 py-1 border"
                    style={{ borderColor: "#F5C6C3" }}
                  >
                    {children}
                  </td>
                ),
                del: ({ children }) => (
                  <del className="text-gray-400">{children}</del>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {isUser && timestamp && (
          <span className="mt-1 px-1 text-[11px] text-gray-500 opacity-55">
            {timestamp}
          </span>
        )}

        {!isUser && !showAssistantLoading && message.content.trim() && (
          <button
            type="button"
            onClick={handleCopy}
            className="mt-1 inline-flex items-center gap-1 px-1 text-[11px] text-gray-400 opacity-80 transition hover:text-gray-500"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? "Copied" : "Copy"}</span>
          </button>
        )}
      </div>
    </div>
  );
}

function formatMessageTime(createdAt?: string): string {
  if (!createdAt) return "";

  const parsed = new Date(createdAt);
  if (Number.isNaN(parsed.getTime())) return "";

  return parsed.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}
