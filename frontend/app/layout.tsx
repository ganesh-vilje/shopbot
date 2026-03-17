import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShopBot — AI Shopping Assistant",
  description: "Your intelligent e-commerce assistant powered by AI",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
