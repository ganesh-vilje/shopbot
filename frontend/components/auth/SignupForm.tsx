"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, Eye, EyeOff, Loader2, ShoppingBag } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

function PasswordRule({ met, text }: { met: boolean; text: string }) {
  return (
    <li className="flex items-center gap-1.5 text-xs" style={{ color: met ? "#16A34A" : "#9CA3AF" }}>
      <CheckCircle2 size={12} style={{ opacity: met ? 1 : 0.4 }} />
      {text}
    </li>
  );
}

export default function SignupForm() {
  const { signup } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const pw = form.password;
  const rules = {
    length: pw.length >= 8,
    upper: /[A-Z]/.test(pw),
    number: /\d/.test(pw),
    match: pw === form.confirm && pw.length > 0,
  };
  const pwValid = Object.values(rules).every(Boolean);

  function set(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((current) => ({ ...current, [key]: e.target.value }));
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pwValid) {
      setError("Please fix the password issues above.");
      return;
    }

    setError("");
    setLoading(true);
    try {
      await signup(form.name, form.email, form.password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = { borderColor: "#D1D5DB" };
  const focusStyle = { borderColor: "#C0392B" };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-white px-4 py-8">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-xl">
          <div className="mb-7 flex flex-col items-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "#C0392B" }}>
              <ShoppingBag size={28} color="white" />
            </div>
            <h1 className="text-2xl font-bold" style={{ color: "#C0392B" }}>ShopBot</h1>
            <p className="mt-1 text-sm text-gray-500">Create your account</p>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
              <AlertCircle size={16} style={{ color: "#C0392B" }} />
              <p className="text-sm" style={{ color: "#C0392B" }}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Name</label>
              <input
                required
                disabled={loading}
                value={form.name}
                onChange={set("name")}
                placeholder="Enter your name"
                className="w-full rounded-lg border px-4 py-3 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                style={inputStyle}
                onFocus={(e) => Object.assign(e.target.style, focusStyle)}
                onBlur={(e) => Object.assign(e.target.style, inputStyle)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Email address</label>
              <input
                type="email"
                required
                disabled={loading}
                value={form.email}
                onChange={set("email")}
                placeholder="you@example.com"
                className="w-full rounded-lg border px-4 py-3 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                style={inputStyle}
                onFocus={(e) => Object.assign(e.target.style, focusStyle)}
                onBlur={(e) => Object.assign(e.target.style, inputStyle)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  disabled={loading}
                  value={form.password}
                  onChange={set("password")}
                  placeholder="Create a password"
                  className="w-full rounded-lg border px-4 py-3 pr-11 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, focusStyle)}
                  onBlur={(e) => Object.assign(e.target.style, inputStyle)}
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setShowPw((value) => !value)}
                  className="absolute right-3 top-3.5 text-gray-400 transition-colors disabled:cursor-not-allowed"
                >
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {pw && (
                <ul className="mt-2 space-y-1 pl-1">
                  <PasswordRule met={rules.length} text="At least 8 characters" />
                  <PasswordRule met={rules.upper} text="One uppercase letter" />
                  <PasswordRule met={rules.number} text="One number" />
                </ul>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Confirm Password</label>
              <input
                type="password"
                required
                disabled={loading}
                value={form.confirm}
                onChange={set("confirm")}
                placeholder="Repeat your password"
                className="w-full rounded-lg border px-4 py-3 text-sm focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                style={inputStyle}
                onFocus={(e) => Object.assign(e.target.style, focusStyle)}
                onBlur={(e) => Object.assign(e.target.style, inputStyle)}
              />
              {form.confirm && !rules.match && (
                <p className="mt-1 text-xs" style={{ color: "#C0392B" }}>Passwords don&apos;t match</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !pwValid}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold text-white transition-all active:scale-95 disabled:cursor-not-allowed disabled:opacity-70"
              style={{ background: "#C0392B" }}
              onMouseEnter={(e) => {
                if (!loading && pwValid) {
                  (e.target as HTMLButtonElement).style.background = "#922B21";
                }
              }}
              onMouseLeave={(e) => {
                if (!loading && pwValid) {
                  (e.target as HTMLButtonElement).style.background = "#C0392B";
                }
              }}
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <a href="/login" className="font-semibold" style={{ color: "#C0392B" }}>Sign In</a>
          </p>
        </div>
      </div>
    </div>
  );
}
