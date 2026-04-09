"use client";

import { Loader2 } from "lucide-react";

type AuthLoadingOverlayProps = {
  title: string;
  message: string;
  hint: string;
};

export default function AuthLoadingOverlay({ title, message, hint }: AuthLoadingOverlayProps) {
  return (
    <div className="absolute inset-0 z-20 rounded-2xl bg-white/80 backdrop-blur-sm">
      <div className="flex h-full flex-col items-center justify-center px-8 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-red-100 bg-red-50 shadow-sm">
          <Loader2 size={28} className="animate-spin" style={{ color: "#C0392B" }} />
        </div>
        <p className="text-lg font-semibold text-gray-900">{title}</p>
        <p className="mt-2 text-sm leading-6 text-gray-600">{message}</p>

        <div className="mt-6 w-full max-w-xs">
          <div className="h-2 overflow-hidden rounded-full bg-gray-200">
            <div
              className="auth-loading-bar h-full w-1/2 rounded-full"
              style={{ background: "linear-gradient(90deg, #C0392B 0%, #E57373 100%)" }}
            />
          </div>
          <p className="mt-2 text-xs font-medium uppercase tracking-[0.2em] text-gray-400">
            {hint}
          </p>
        </div>
      </div>

      <style jsx global>{`
        @keyframes auth-loading-slide {
          0% {
            transform: translateX(-90%);
          }
          100% {
            transform: translateX(190%);
          }
        }

        .auth-loading-bar {
          animation: auth-loading-slide 1.35s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
