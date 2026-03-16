"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ShoppingBag } from "lucide-react";
import type { Message } from "@/types";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`message-enter flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" style={{background:"#C0392B"}}>
          <ShoppingBag size={14} color="white" />
        </div>
      )}

      {/* Bubble */}
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? "rounded-tr-sm text-white"
          : "rounded-tl-sm text-gray-800"
      }`}
        style={isUser
          ? {background:"#C0392B"}
          : {background:"#F9EBEA", border:"1px solid #F5C6C3"}
        }
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({children}) => <ul className="list-disc ml-4 mb-2 space-y-1">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal ml-4 mb-2 space-y-1">{children}</ol>,
              li: ({children}) => <li>{children}</li>,
              strong: ({children}) => <strong className="font-semibold" style={{color:"#922B21"}}>{children}</strong>,
              a: ({href, children}) => <a href={href} className="underline" style={{color:"#C0392B"}} target="_blank" rel="noreferrer">{children}</a>,
              table: ({children}) => <div className="overflow-x-auto my-2"><table className="text-xs border-collapse w-full">{children}</table></div>,
              th: ({children}) => <th className="px-2 py-1 text-left font-semibold border" style={{background:"#F9EBEA",borderColor:"#F5C6C3"}}>{children}</th>,
              td: ({children}) => <td className="px-2 py-1 border" style={{borderColor:"#F5C6C3"}}>{children}</td>,
              del: ({children}) => <del className="text-gray-400">{children}</del>,
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
