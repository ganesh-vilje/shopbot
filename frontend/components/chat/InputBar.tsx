"use client";
import { useRef, useEffect, useState } from "react";
import { Send, Mic } from "lucide-react";
interface InputBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export default function InputBar({
  value,
  onChange,
  onSubmit,
  disabled,
}: InputBarProps) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [isListening, setIsListening] = useState(false);

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
const audioRef = useRef<HTMLAudioElement | null>(null);

useEffect(() => {
  audioRef.current = new Audio(
    new URL("../../assets/micon.mp3", import.meta.url).href
  );
}, []);

const playMicSound = () => {
  audioRef.current?.play();
};

const handleVoiceClick = () => {
  playMicSound();   // 🔊 play sound
  handleVoice();    // existing function
};
  function handleVoice() {
    if (
      !("webkitSpeechRecognition" in window) &&
      !("SpeechRecognition" in window)
    ) {
      alert("Speech recognition not supported in this browser");
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      onChange(value + (value ? " " : "") + transcript);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div
          className="flex items-end gap-2 px-4 py-2 rounded-lg transition-all"
          style={{ border: "2px solid transparent" }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLElement).style.borderColor = "#C0392B")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLElement).style.borderColor = "transparent")
          }
        >
          <textarea
            ref={ref}
            rows={1}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKey}
            disabled={disabled}
            placeholder="Ask about your orders, products, account…"
            className="flex-1 resize-none bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none px-1 text-left"
            style={{ paddingBottom: "6px", fontFamily: "sans-serif" }}
          />

        <div className="relative">
  {!isListening ? (
    <div className="relative">
      <button
        onClick={handleVoiceClick}
        disabled={disabled}
        className="peer flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-90"
        style={{
          background: disabled ? "#E5E7EB" : "#C0392B"
        }}
        onMouseEnter={e => {
          if (!disabled) {
            (e.currentTarget as HTMLElement).style.background = "#922B21";
          }
        }}
        onMouseLeave={e => {
          if (!disabled) {
            (e.currentTarget as HTMLElement).style.background = "#C0392B";
          }
        }}
      >
        <Mic size={16} color={disabled ? "#9CA3AF" : "white"} />
      </button>

      {/* Tooltip */}
      {!disabled && (
        <span
          className="absolute bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap px-2 py-1 text-xs rounded-md opacity-0 peer-hover:opacity-100 transition-all pointer-events-none"
          style={{ background: "black", color: "white" }}
        >
          Voice input
        </span>
      )}
    </div>
  ) : (
    <div
      className="flex items-center gap-2 px-3 h-9 rounded-xl"
      style={{ background: "#FEF3C7" }}
    >
      <Mic size={16} color="#d93006" />

      <div className="flex gap-1">
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: "#D97706",
            animation: "pulse 1s infinite"
          }}
        ></span>
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: "#D97706",
            animation: "pulse 1s infinite 0.2s"
          }}
        ></span>
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: "#D97706",
            animation: "pulse 1s infinite 0.4s"
          }}
        ></span>
      </div>

      <button
        onClick={handleVoice}
        className="text-xs font-medium transition-all ml-1"
        style={{ color: "#d93006" }}
        onMouseEnter={(e) =>
          ((e.currentTarget as HTMLElement).style.color = "#B45309")
        }
        onMouseLeave={(e) =>
          ((e.currentTarget as HTMLElement).style.color = "#d93006")
        }
      >
        Cancel
      </button>
    </div>
  )}

  <style jsx>{`
    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.4;
      }
    }
  `}</style>
</div>
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-90"
            style={{
              background: disabled || !value.trim() ? "#E5E7EB" : "#C0392B",
            }}
            onMouseEnter={(e) => {
              if (!disabled && value.trim())
                (e.currentTarget as HTMLElement).style.background = "#922B21";
            }}
            onMouseLeave={(e) => {
              if (!disabled && value.trim())
                (e.currentTarget as HTMLElement).style.background = "#C0392B";
            }}
          >
            <Send
              size={16}
              color={disabled || !value.trim() ? "#9CA3AF" : "white"}
            />
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
