"use client";

import { forwardRef, useEffect, useRef, useState, type MutableRefObject } from "react";
import { Mic, Send } from "lucide-react";

interface InputBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (text: string) => void;
  disabled?: boolean;
}

type BrowserSpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onstart: null | (() => void);
  onend: null | (() => void);
  onresult: null | ((event: any) => void);
  onerror: null | ((event: any) => void);
};

const InputBar = forwardRef<HTMLTextAreaElement, InputBarProps>(function InputBar(
  { value, onChange, onSubmit, disabled },
  forwardedRef
) {
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const ignoreSpeechResultsRef = useRef(false);
  const [isListening, setIsListening] = useState(false);

  function setTextAreaRef(node: HTMLTextAreaElement | null) {
    textAreaRef.current = node;

    if (typeof forwardedRef === "function") {
      forwardedRef(node);
    } else if (forwardedRef) {
      (forwardedRef as MutableRefObject<HTMLTextAreaElement | null>).current = node;
    }
  }

  useEffect(() => {
    if (!textAreaRef.current) return;

    textAreaRef.current.style.height = "auto";
    textAreaRef.current.style.height =
      Math.min(textAreaRef.current.scrollHeight, 140) + "px";
  }, [value]);

  useEffect(() => {
    audioRef.current = new Audio(
      new URL("../../assets/micon.mp3", import.meta.url).href
    );
  }, []);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    const recognition: BrowserSpeechRecognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      ignoreSpeechResultsRef.current = false;
      setIsListening(true);
    };
    recognition.onend = () => {
      ignoreSpeechResultsRef.current = false;
      setIsListening(false);
    };
    recognition.onresult = (event) => {
      if (ignoreSpeechResultsRef.current) return;

      let transcript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      onChange(transcript);
    };
    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [onChange]);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) handleSubmit();
    }
  }

  function playMicSound() {
    audioRef.current?.play().catch(() => {
      // Ignore browser autoplay rejections for the UI click sound.
    });
  }

  function handleVoiceClick() {
    playMicSound();

    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  }

  function handleSubmit() {
    const text = value.trim();
    if (!text || disabled) return;

    if (isListening && recognitionRef.current) {
      ignoreSpeechResultsRef.current = true;
      recognitionRef.current.stop();
    }

    onSubmit(text);
    onChange("");
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="mx-auto max-w-3xl">
        <div
          className="flex items-end gap-2 rounded-lg px-4 py-2 transition-all"
          style={{
            border: "2px solid transparent",
            boxShadow: "inset 0 0 0 1px #C0392B",
          }}
          onMouseEnter={(e) => {
            const el = e.currentTarget as HTMLElement;
            el.style.boxShadow = "inset 0 0 0 2px #C0392B";
          }}
          onMouseLeave={(e) => {
            const el = e.currentTarget as HTMLElement;
            el.style.boxShadow = "inset 0 0 0 1px #C0392B";
          }}
        >
          <textarea
            ref={setTextAreaRef}
            rows={1}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about your orders, products, account..."
            className="flex-1 resize-none bg-transparent px-1 text-left text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
            style={{ paddingBottom: "6px", fontFamily: "sans-serif" }}
          />

          <div className="relative">
            {!isListening ? (
              <div className="relative">
                <button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={handleVoiceClick}
                  disabled={disabled}
                  className="peer flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl transition-all active:scale-90 disabled:cursor-not-allowed disabled:opacity-40"
                  style={{ background: disabled ? "#E5E7EB" : "#C0392B" }}
                  type="button"
                  onMouseEnter={(e) => {
                    if (!disabled) {
                      (e.currentTarget as HTMLElement).style.background =
                        "#922B21";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!disabled) {
                      (e.currentTarget as HTMLElement).style.background =
                        "#C0392B";
                    }
                  }}
                >
                  <Mic size={16} color={disabled ? "#9CA3AF" : "white"} />
                </button>

                {!disabled && (
                  <span
                    className="pointer-events-none absolute bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md px-2 py-1 text-xs opacity-0 transition-all peer-hover:opacity-100"
                    style={{ background: "black", color: "white" }}
                  >
                    Voice input
                  </span>
                )}
              </div>
            ) : (
              <div
                className="flex h-9 items-center gap-2 rounded-xl px-3"
                style={{ background: "#FEF3C7" }}
              >
                <Mic size={16} color="#D93006" />

                <div className="flex gap-1">
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{
                      background: "#D97706",
                      animation: "pulse 1s infinite",
                    }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{
                      background: "#D97706",
                      animation: "pulse 1s infinite 0.2s",
                    }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full"
                    style={{
                      background: "#D97706",
                      animation: "pulse 1s infinite 0.4s",
                    }}
                  />
                </div>

                <button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={handleVoiceClick}
                  className="ml-1 text-xs font-medium transition-all"
                  style={{ color: "#D93006" }}
                  type="button"
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.color = "#B45309";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.color = "#D93006";
                  }}
                >
                  Cancel
                </button>
              </div>
            )}

            <style jsx>{`
              @keyframes pulse {
                0%,
                100% {
                  opacity: 1;
                }
                50% {
                  opacity: 0.4;
                }
              }
            `}</style>
          </div>

          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl transition-all active:scale-90 disabled:cursor-not-allowed disabled:opacity-40"
            style={{
              background: disabled || !value.trim() ? "#E5E7EB" : "#C0392B",
            }}
            type="button"
            onMouseEnter={(e) => {
              if (!disabled && value.trim()) {
                (e.currentTarget as HTMLElement).style.background = "#922B21";
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled && value.trim()) {
                (e.currentTarget as HTMLElement).style.background = "#C0392B";
              }
            }}
          >
            <Send
              size={16}
              color={disabled || !value.trim() ? "#9CA3AF" : "white"}
            />
          </button>
        </div>

        <p className="mt-2 text-center text-xs text-gray-400">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
});

export default InputBar;
