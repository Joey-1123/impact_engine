import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Impact Engine", template: "%s — Impact Engine" },
  description: "Codebase intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
