"use client";
import { useState } from "react";
import { Eye, EyeOff, ShoppingBag, AlertCircle, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getApiUrl } from "@/lib/api";

function PasswordRule({ met, text }: { met: boolean; text: string }) {
  return (
    <li className="flex items-center gap-1.5 text-xs" style={{color: met ? "#16A34A" : "#9CA3AF"}}>
      <CheckCircle2 size={12} style={{opacity: met ? 1 : 0.4}} />
      {text}
    </li>
  );
}

export default function SignupForm() {
  const { signup } = useAuth();
  const [form, setForm] = useState({ full_name:"", email:"", password:"", confirm:"" });
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

  function set(k: keyof typeof form) { return (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({...f, [k]: e.target.value})); }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pwValid) { setError("Please fix the password issues above."); return; }
    setError(""); setLoading(true);
    try { await signup(form.full_name, form.email, form.password); }
    catch (err: unknown) { setError(err instanceof Error ? err.message : "Signup failed"); }
    finally { setLoading(false); }
  }

  const inputStyle = { borderColor: "#D1D5DB" };
  const focusStyle = { borderColor: "#C0392B" };


  async function handleGoogleLogin() {
    window.location.href = getApiUrl("/auth/oauth/google");
  }
  
  async function handleGitHubLogin() {
    window.location.href = getApiUrl("/auth/oauth/github");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-white px-4 py-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
          {/* Brand */}
          <div className="flex flex-col items-center mb-7">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3" style={{background:"#C0392B"}}>
              <ShoppingBag size={28} color="white" />
            </div>
            <h1 className="text-2xl font-bold" style={{color:"#C0392B"}}>ShopBot</h1>
            <p className="text-gray-500 text-sm mt-1">Create your account</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg mb-4 bg-red-50 border border-red-200">
              <AlertCircle size={16} style={{color:"#C0392B"}} />
              <p className="text-sm" style={{color:"#C0392B"}}>{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input required value={form.full_name} onChange={set("full_name")} placeholder="Jane Smith"
                className="w-full px-4 py-3 rounded-lg border text-sm focus:outline-none"
                style={inputStyle} onFocus={e => Object.assign(e.target.style, focusStyle)} onBlur={e => Object.assign(e.target.style, inputStyle)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
              <input type="email" required value={form.email} onChange={set("email")} placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-lg border text-sm focus:outline-none"
                style={inputStyle} onFocus={e => Object.assign(e.target.style, focusStyle)} onBlur={e => Object.assign(e.target.style, inputStyle)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input type={showPw ? "text" : "password"} required value={form.password} onChange={set("password")} placeholder="••••••••"
                  className="w-full px-4 py-3 pr-11 rounded-lg border text-sm focus:outline-none"
                  style={inputStyle} onFocus={e => Object.assign(e.target.style, focusStyle)} onBlur={e => Object.assign(e.target.style, inputStyle)} />
                <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-3.5 text-gray-400">
                  {showPw ? <EyeOff size={18}/> : <Eye size={18}/>}
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <input type="password" required value={form.confirm} onChange={set("confirm")} placeholder="••••••••"
                className="w-full px-4 py-3 rounded-lg border text-sm focus:outline-none"
                style={inputStyle} onFocus={e => Object.assign(e.target.style, focusStyle)} onBlur={e => Object.assign(e.target.style, inputStyle)} />
              {form.confirm && !rules.match && (
                <p className="text-xs mt-1" style={{color:"#C0392B"}}>Passwords don&apos;t match</p>
              )}
            </div>

            <button type="submit" disabled={loading || !pwValid}
              className="w-full py-3 rounded-lg font-semibold text-white text-sm transition-all active:scale-95 disabled:opacity-60 mt-2"
              style={{background:"#C0392B"}}
              onMouseEnter={e => (e.target as HTMLButtonElement).style.background = "#922B21"}
              onMouseLeave={e => (e.target as HTMLButtonElement).style.background = "#C0392B"}
            >
              {loading ? "Creating account…" : "Create Account"}
            </button>
          </form>

          <div className="my-5 flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400 font-medium">OR</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <div className="space-y-3">
            <button onClick={handleGoogleLogin} className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-lg border-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors" style={{borderColor:"#C0392B"}}>
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Continue with Google
            </button>
            <button onClick={handleGitHubLogin} className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-lg border-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors" style={{borderColor:"#C0392B"}}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              Continue with GitHub
            </button>
          </div>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <a href="/login" className="font-semibold" style={{color:"#C0392B"}}>Sign In</a>
          </p>
        </div>
      </div>
    </div>
  );
}
