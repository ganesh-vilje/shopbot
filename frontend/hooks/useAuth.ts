"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setTokens, setUser, clearTokens, getUser } from "@/lib/api";
import type { User } from "@/types";

export function useAuth() {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const u = getUser();
    setUserState(u);
    setLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const res = await api.post<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>("/auth/login", { email, password });
    setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
    setUserState(res.user);
    router.push("/dashboard");
  }

  async function signup(full_name: string, email: string, password: string) {
    const res = await api.post<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>("/auth/signup", { full_name, email, password });
    setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
    setUserState(res.user);
    router.push("/dashboard");
  }

  async function logout() {
    const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    if (refresh) {
      await api.post("/auth/logout", { refresh_token: refresh }).catch(() => {});
    }
    clearTokens();
    setUserState(null);
    router.push("/login");
  }

  return { user, loading, login, signup, logout };
}
