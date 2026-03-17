"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { setTokens, setUser } from "@/lib/api";

export default function OAuthSuccess() {
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token  = params.get("token");

    if (token) {
      setTokens(token);
      // Fetch user info with the token
      fetch("http://localhost:8000/api/me", {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
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