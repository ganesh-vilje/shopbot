"use client";

import { useState } from "react";
import { AlertCircle, Eye, EyeOff, Loader2, ShoppingBag } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";

export default function LoginForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-xl">
          <div className="mb-8 flex flex-col items-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "#C0392B" }}>
              <ShoppingBag size={28} color="white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: "#C0392B" }}>ShopBot</h1>
            <p className="mt-1 text-sm text-gray-500">Sign in to your account</p>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
              <AlertCircle size={16} style={{ color: "#C0392B" }} />
              <p className="text-sm" style={{ color: "#C0392B" }}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Email address</label>
              <input
                type="email"
                required
                disabled={loading}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                onFocus={(e) => { e.target.style.borderColor = "#C0392B"; }}
                onBlur={(e) => { e.target.style.borderColor = "#D1D5DB"; }}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  disabled={loading}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 pr-11 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                  onFocus={(e) => { e.target.style.borderColor = "#C0392B"; }}
                  onBlur={(e) => { e.target.style.borderColor = "#D1D5DB"; }}
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setShowPw((value) => !value)}
                  className="absolute right-3 top-3.5 text-gray-400 transition-colors hover:text-gray-600 disabled:cursor-not-allowed"
                >
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold text-white transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-70"
              style={{ background: loading ? "#E57373" : "#C0392B" }}
              onMouseEnter={(e) => {
                if (!loading) {
                  (e.target as HTMLButtonElement).style.background = "#922B21";
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  (e.target as HTMLButtonElement).style.background = "#C0392B";
                }
              }}
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Don&apos;t have an account?{" "}
            <a href="/signup" className="font-semibold" style={{ color: "#C0392B" }}>Sign Up</a>
          </p>
        </div>
      </div>
    </div>
  );
}
