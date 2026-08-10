import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SecondBrain AI",
  description: "RAG workspace for ingesting, retrieving, and chatting with your knowledge base",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f6f8fb] text-slate-950 antialiased">
        {children}
      </body>
    </html>
  );
}