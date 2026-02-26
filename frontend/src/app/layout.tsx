import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SecondBrain",
  description: "AI second brain for ingest + chat",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
            <div className="text-lg font-semibold text-indigo-600">
              SecondBrain
            </div>
            <div className="text-sm text-slate-500">
              AI ingest + chat
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}