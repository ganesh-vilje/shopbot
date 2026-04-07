"use client";

import { useState } from "react";
import { AlertCircle, Eye, EyeOff, ShoppingBag } from "lucide-react";

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
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3" style={{ background: "#C0392B" }}>
              <ShoppingBag size={28} color="white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: "#C0392B" }}>ShopBot</h1>
            <p className="text-gray-500 text-sm mt-1">Sign in to your account</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg mb-4 bg-red-50 border border-red-200">
              <AlertCircle size={16} style={{ color: "#C0392B" }} />
              <p className="text-sm" style={{ color: "#C0392B" }}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none text-sm"
                onFocus={(e) => { e.target.style.borderColor = "#C0392B"; }}
                onBlur={(e) => { e.target.style.borderColor = "#D1D5DB"; }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 pr-11 rounded-lg border border-gray-300 focus:outline-none text-sm"
                  onFocus={(e) => { e.target.style.borderColor = "#C0392B"; }}
                  onBlur={(e) => { e.target.style.borderColor = "#D1D5DB"; }}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((value) => !value)}
                  className="absolute right-3 top-3.5 text-gray-400 hover:text-gray-600"
                >
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-white text-sm transition-all active:scale-95 disabled:opacity-60"
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
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Don&apos;t have an account?{" "}
            <a href="/signup" className="font-semibold" style={{ color: "#C0392B" }}>Sign Up</a>
          </p>
        </div>
      </div>
    </div>
  );
}
