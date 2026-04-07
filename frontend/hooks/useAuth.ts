"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setUser, clearSession, getUser } from "@/lib/api";
import type { User } from "@/types";

function clearChatSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("active_conv_id");
}

export function useAuth() {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const cachedUser = getUser();
    if (cachedUser) setUserState(cachedUser);

    api.get<User>("/api/me")
      .then((me) => {
        setUser(me);
        setUserState(me);
      })
      .catch(() => {
        clearSession();
        setUserState(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const res = await api.post<{ user: User }>("/auth/login", { email, password });
    clearChatSession();
    setUser(res.user);
    setUserState(res.user);
    router.push("/dashboard");
  }

  async function signup(full_name: string, email: string, password: string) {
    const res = await api.post<{ user: User }>("/auth/signup", { full_name, email, password });
    clearChatSession();
    setUser(res.user);
    setUserState(res.user);
    router.push("/dashboard");
  }

  async function logout() {
    await api.post("/auth/logout").catch(() => {});
    clearChatSession();
    clearSession();
    setUserState(null);
    router.push("/login");
  }

  return { user, loading, login, signup, logout };
}
