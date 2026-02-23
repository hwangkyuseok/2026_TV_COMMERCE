import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "TV Commerce",
  description: "Smart TV Commerce & Recommendation Platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-tv-bg text-tv-text w-screen h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
