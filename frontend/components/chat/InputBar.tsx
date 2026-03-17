"use client";
import { useRef, useEffect } from "react";
import { Send } from "lucide-react";

interface InputBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export default function InputBar({ value, onChange, onSubmit, disabled }: InputBarProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = Math.min(ref.current.scrollHeight, 140) + "px";
    }
  }, [value]);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-2 px-4 py-2 rounded-lg transition-all" style={{border:"2px solid transparent"}} onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = "#C0392B"} onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = "transparent"}
        >
          <textarea
            ref={ref}
            rows={1}
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKey}
            disabled={disabled}
            placeholder="Ask about your orders, products, account…"
            className="flex-1 resize-none bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none px-1 text-left"
            style={{paddingBottom:"6px", fontFamily:"sans-serif"}}
          />
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-90"
            style={{background: disabled || !value.trim() ? "#E5E7EB" : "#C0392B"}}
            onMouseEnter={e => { if (!disabled && value.trim()) (e.currentTarget as HTMLElement).style.background = "#922B21"; }}
            onMouseLeave={e => { if (!disabled && value.trim()) (e.currentTarget as HTMLElement).style.background = "#C0392B"; }}
          >
            <Send size={16} color={disabled || !value.trim() ? "#9CA3AF" : "white"} />
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
