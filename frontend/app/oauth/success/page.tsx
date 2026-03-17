"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, setTokens, setUser } from "@/lib/api";
import type { User } from "@/types";

export default function OAuthSuccess() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get("token");
    const refreshToken = params.get("refresh_token");

    if (accessToken) {
      setTokens(accessToken, refreshToken || undefined);
      api.get<User>("/api/me")
        .then(user => {
          setUser(user);
          router.push("/dashboard");
        })
        .catch(() => router.push("/login"));
    } else {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-4 border-t-transparent animate-spin"
        style={{ borderColor: "#C0392B", borderTopColor: "transparent" }} />
    </div>
  );
}
