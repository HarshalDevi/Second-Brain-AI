"use client";

import { useState } from "react";
import {
  Bot,
  Database,
  FilePlus2,
  Library,
  MessageSquareText,
  SearchCheck,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { ChatPanel } from "@/components/ChatPanel";
import { IngestPanel } from "@/components/IngestPanel";
import { DocumentsPanel } from "@/components/DocumentsPanel";

type Tab = "chat" | "ingest" | "docs";

const tabs: Array<{
  id: Tab;
  label: string;
  description: string;
  icon: typeof MessageSquareText;
}> = [
  {
    id: "chat",
    label: "Chat",
    description: "Ask with grounded sources",
    icon: MessageSquareText,
  },
  {
    id: "ingest",
    label: "Ingest",
    description: "Add notes, URLs, files, audio",
    icon: FilePlus2,
  },
  {
    id: "docs",
    label: "Library",
    description: "Inspect stored chunks",
    icon: Library,
  },
];

const stats = [
  { label: "Hybrid retrieval", value: "Vector + keyword", icon: SearchCheck },
  { label: "Responses", value: "Streaming", icon: Sparkles },
  { label: "Grounding", value: "Cited chunks", icon: ShieldCheck },
];

export default function Page() {
  const [tab, setTab] = useState<Tab>("chat");
  const activeTab = tabs.find((item) => item.id === tab) ?? tabs[0];

  return (
    <main className="min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-sm">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-normal text-slate-950">
                SecondBrain AI
              </h1>
              <p className="text-sm text-slate-500">
                Ingest, retrieve, and answer from your private knowledge base
              </p>
            </div>
          </div>

          <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[560px]">
            {stats.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center gap-3 rounded-2xl bg-white px-3 py-2 ring-1 ring-slate-200"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700 ring-1 ring-cyan-100">
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-xs text-slate-500">{item.label}</div>
                    <div className="truncate text-sm font-medium text-slate-900">{item.value}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </header>

        <div className="grid flex-1 gap-5 py-5 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)]">
            <nav className="grid gap-2 rounded-2xl bg-white p-2 ring-1 ring-slate-200">
              {tabs.map((item) => {
                const Icon = item.icon;
                const active = item.id === tab;
                return (
                  <button
                    key={item.id}
                    onClick={() => setTab(item.id)}
                    className={[
                      "flex min-h-16 items-center gap-3 rounded-xl px-3 text-left transition",
                      active
                        ? "bg-slate-950 text-white shadow-sm"
                        : "text-slate-700 hover:bg-slate-50",
                    ].join(" ")}
                  >
                    <span
                      className={[
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ring-1",
                        active
                          ? "bg-white/10 text-white ring-white/15"
                          : "bg-slate-50 text-slate-600 ring-slate-200",
                      ].join(" ")}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-medium">{item.label}</span>
                      <span
                        className={[
                          "block truncate text-xs",
                          active ? "text-slate-300" : "text-slate-500",
                        ].join(" ")}
                      >
                        {item.description}
                      </span>
                    </span>
                  </button>
                );
              })}
            </nav>

            <div className="mt-4 rounded-2xl bg-white p-4 ring-1 ring-slate-200">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
                <Database className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                RAG Pipeline
              </div>
              <div className="mt-3 grid gap-2 text-xs text-slate-600">
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2">
                  <span>Chunking</span>
                  <span className="font-medium text-slate-800">Paragraph-aware</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2">
                  <span>Search</span>
                  <span className="font-medium text-slate-800">Hybrid</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2">
                  <span>Citations</span>
                  <span className="font-medium text-slate-800">Evidence cards</span>
                </div>
              </div>
            </div>
          </aside>

          <section className="min-w-0">
            <div className="mb-4 flex flex-col gap-1">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-cyan-700">
                {activeTab.label}
              </p>
              <h2 className="text-2xl font-semibold tracking-normal text-slate-950">
                {activeTab.description}
              </h2>
            </div>

            {tab === "chat" && <ChatPanel />}
            {tab === "ingest" && <IngestPanel />}
            {tab === "docs" && <DocumentsPanel />}
          </section>
        </div>
      </div>
    </main>
  );
}