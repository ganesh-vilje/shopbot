import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShopBot — AI Shopping Assistant",
  description: "Your intelligent e-commerce assistant powered by AI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
